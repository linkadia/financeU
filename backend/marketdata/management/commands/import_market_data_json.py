import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from marketdata.services import import_market_data_from_gemini_payload


class Command(BaseCommand):
    help = "Import market data from a Gemini-style JSON payload file."

    def add_arguments(self, parser):
        parser.add_argument("json_path", help="Path to the market data JSON file.")

    def handle(self, *args, **options):
        json_path = Path(options["json_path"])

        if not json_path.exists():
            raise CommandError(f"JSON file does not exist: {json_path}")

        if not json_path.is_file():
            raise CommandError(f"JSON path is not a file: {json_path}")

        try:
            with json_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except json.JSONDecodeError as error:
            raise CommandError(f"Invalid JSON in {json_path}: {error}") from error

        if not isinstance(payload, dict):
            raise CommandError("Market data JSON payload must be an object.")

        run = import_market_data_from_gemini_payload(payload)

        self.stdout.write("Market data import complete.")
        self.stdout.write(f"Run id: {run.id}")
        self.stdout.write(f"Status: {run.status}")
        self.stdout.write(f"Items received: {run.items_received}")
        self.stdout.write(f"Items imported: {run.items_imported}")
        self.stdout.write(f"Items updated: {run.items_updated}")
        self.stdout.write(f"Items skipped: {run.items_skipped}")
        self.stdout.write(f"Items failed: {run.items_failed}")
