import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from .models import FinancialDataRun, FinancialProduct, FinancialProductSnapshot

logger = logging.getLogger(__name__)

EXPECTED_COLS = {"s", "v", "pv", "t", "pt", "src", "url", "q"}
USABLE_SNAPSHOT_STATUSES = {
    FinancialProductSnapshot.ValidationStatus.VALID,
    FinancialProductSnapshot.ValidationStatus.PARTIAL,
}


def parse_decimal(value):
    if value is None or value == "":
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def parse_temporal_value(value):
    if value is None or value == "":
        return None, None, None

    raw = str(value).strip()

    try:
        if "-Q" in raw:
            year, quarter = raw.split("-Q", 1)
            month = ((int(quarter) - 1) * 3) + 1
            return raw, date(int(year), month, 1), None

        if len(raw) == 7 and raw[4] == "-":
            year, month = raw.split("-", 1)
            return raw, date(int(year), int(month), 1), None

        if len(raw) == 10:
            parsed_date = date.fromisoformat(raw)
            return raw, parsed_date, None

        parsed_datetime = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if timezone.is_naive(parsed_datetime):
            parsed_datetime = timezone.make_aware(parsed_datetime, timezone.get_current_timezone())
        return raw, parsed_datetime.date(), parsed_datetime
    except (TypeError, ValueError):
        return raw, None, None


def parse_quality(value):
    if value is None or value == "":
        return None, None

    numeric = parse_decimal(value)
    if numeric is not None and Decimal("0") <= numeric <= Decimal("1"):
        return numeric, None

    return None, None


def calculate_change(current_value, previous_value):
    if current_value is None or previous_value is None:
        return None, None

    change_absolute = current_value - previous_value
    if previous_value == 0:
        return change_absolute, None

    change_percent = (change_absolute / previous_value) * Decimal("100")
    return change_absolute, change_percent


def row_validation_status(current_value, effective_date, effective_datetime, errors):
    if current_value is None:
        errors.append("Missing or invalid current_value")

    if effective_date is None and effective_datetime is None:
        errors.append("Missing or invalid effective_at")

    if current_value is None and (effective_date is None and effective_datetime is None):
        return FinancialProductSnapshot.ValidationStatus.INVALID

    if errors:
        return FinancialProductSnapshot.ValidationStatus.PARTIAL

    return FinancialProductSnapshot.ValidationStatus.VALID


def snapshot_has_market_data(snapshot):
    return (
        snapshot is not None
        and snapshot.validation_status in USABLE_SNAPSHOT_STATUSES
        and snapshot.current_value is not None
        and bool(snapshot.effective_at_raw)
    )


def sync_featured_products_from_latest_snapshots():
    for product in FinancialProduct.objects.filter(is_active=True):
        latest_snapshot = (
            product.snapshots.order_by("-effective_datetime", "-effective_date", "-created_at")
            .first()
        )
        should_be_featured = snapshot_has_market_data(latest_snapshot)

        if product.is_featured != should_be_featured:
            product.is_featured = should_be_featured
            product.save(update_fields=["is_featured", "updated_at"])


@transaction.atomic
def import_market_data_from_gemini_payload(payload: dict) -> FinancialDataRun:
    started_at = timezone.now()
    top_level_errors = []

    if not isinstance(payload, dict):
        payload = {}
        top_level_errors.append("Payload must be a JSON object")

    cols = payload.get("cols") if isinstance(payload.get("cols"), list) else []
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    gemini_status = str(payload.get("st") or "").upper()

    if not cols:
        top_level_errors.append("Missing or invalid cols")
    elif not EXPECTED_COLS.issubset(set(cols)):
        top_level_errors.append("Payload cols are missing required fields")

    if "rows" not in payload or not isinstance(payload.get("rows"), list):
        top_level_errors.append("Missing or invalid rows")

    requested_at_raw, _, requested_at = parse_temporal_value(payload.get("ts"))

    run = FinancialDataRun.objects.create(
        started_at=started_at,
        provider="gemini",
        requested_at=requested_at,
        items_expected=len(rows),
        items_received=len(rows),
        raw_response=payload,
        errors=list(payload.get("er") or []) + top_level_errors,
    )

    products_by_symbol = {
        product.symbol: product
        for product in FinancialProduct.objects.filter(is_active=True)
    }
    partial_items = 0

    if top_level_errors:
        run.status = FinancialDataRun.Status.FAILED
        run.finished_at = timezone.now()
        run.error_message = "; ".join(top_level_errors)
        run.save(update_fields=["status", "finished_at", "error_message", "errors"])
        return run

    for index, raw_row in enumerate(rows):
        try:
            row = dict(zip(cols, raw_row))
            symbol = str(row.get("s") or "").strip().upper()
            product = products_by_symbol.get(symbol)

            if product is None:
                message = f"Unknown market data symbol rejected: {symbol or '<empty>'}"
                logger.warning(message)
                run.items_skipped += 1
                run.errors.append({"row": index, "symbol": symbol, "error": message})
                continue

            current_value = parse_decimal(row.get("v"))
            previous_value = parse_decimal(row.get("pv"))
            effective_raw, effective_date, effective_datetime = parse_temporal_value(row.get("t"))
            previous_raw, previous_date, previous_datetime = parse_temporal_value(row.get("pt"))
            confidence_score, quality_note = parse_quality(row.get("q"))
            source_url = row.get("url") or None

            if source_url and "vertexaisearch.cloud.google.com/grounding-api-redirect" in source_url:
                source_url = None
                
            if effective_raw is None:
                message = f"Missing effective_at for symbol {symbol}; snapshot was not created"
                run.items_failed += 1
                run.errors.append({"row": index, "symbol": symbol, "error": message, "raw_row": raw_row})
                continue

            validation_errors = []
            validation_status = row_validation_status(
                current_value,
                effective_date,
                effective_datetime,
                validation_errors,
            )
            change_absolute, change_percent = calculate_change(current_value, previous_value)

            _, created = FinancialProductSnapshot.objects.update_or_create(
                product=product,
                effective_at_raw=effective_raw,
                defaults={
                    "run": run,
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "change_absolute": change_absolute,
                    "change_percent": change_percent,
                    "previous_reference_at_raw": previous_raw,
                    "effective_date": effective_date,
                    "previous_reference_date": previous_date,
                    "effective_datetime": effective_datetime,
                    "previous_reference_datetime": previous_datetime,
                    "source_name": (str(row.get("src"))[:160] if row.get("src") else None),
                    "source_url": source_url,
                    "quality_note": quality_note,
                    "confidence_score": confidence_score,
                    "raw_row": raw_row,
                    "validation_status": validation_status,
                    "validation_errors": validation_errors,
                },
            )

            if validation_status == FinancialProductSnapshot.ValidationStatus.INVALID:
                run.items_failed += 1
            else:
                if created:
                    run.items_imported += 1
                else:
                    run.items_updated += 1
                if validation_status == FinancialProductSnapshot.ValidationStatus.PARTIAL:
                    partial_items += 1
        except Exception as error:
            message = f"Failed to import market data row {index}: {error}"
            logger.exception(message)
            run.items_failed += 1
            run.errors.append({"row": index, "error": message, "raw_row": raw_row})

    if run.items_imported == 0 and run.items_updated == 0:
        run.status = FinancialDataRun.Status.FAILED
        run.error_message = "No valid or partial market data rows were imported"
    elif run.items_skipped or run.items_failed or partial_items or gemini_status == FinancialDataRun.Status.PARTIAL_SUCCESS:
        run.status = FinancialDataRun.Status.PARTIAL_SUCCESS
    else:
        run.status = FinancialDataRun.Status.SUCCESS

    run.finished_at = timezone.now()
    run.save()
    sync_featured_products_from_latest_snapshots()
    return run
