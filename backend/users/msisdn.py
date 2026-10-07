import hashlib
import hmac
import re

from django.conf import settings
from rest_framework.exceptions import APIException


SHA256_HEX_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
POLISH_MSISDN_PATTERN = re.compile(r"48[0-9]{9}\Z")
FINGERPRINT_PREFIX = "v1:"


class MsisdnKeyUnavailable(APIException):
    status_code = 503
    default_detail = "Mobile registration is temporarily unavailable."
    default_code = "msisdn_key_not_configured"


def normalize_polish_msisdn(value):
    compact = re.sub(r"[\s()\-]", "", str(value or ""))
    if compact.startswith("+48"):
        compact = compact[1:]
    elif compact.startswith("0048"):
        compact = compact[2:]
    elif len(compact) == 9 and compact.isascii() and compact.isdigit():
        compact = f"48{compact}"

    if not POLISH_MSISDN_PATTERN.fullmatch(compact):
        raise ValueError("Enter a Polish mobile number with 9 digits.")
    return compact


def sha256_msisdn(value):
    normalized = normalize_polish_msisdn(value)
    return hashlib.sha256(normalized.encode("ascii")).hexdigest()


def fingerprint_from_sha256(msisdn_sha256):
    if not isinstance(msisdn_sha256, str) or not SHA256_HEX_PATTERN.fullmatch(msisdn_sha256):
        raise ValueError("msisdn_hash must be a lowercase SHA-256 hex digest.")

    key = settings.MSISDN_HMAC_KEY
    if not key:
        raise MsisdnKeyUnavailable()

    digest = hmac.new(
        key.encode("utf-8"),
        msisdn_sha256.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{FINGERPRINT_PREFIX}{digest}"


def fingerprint_from_msisdn(value):
    return fingerprint_from_sha256(sha256_msisdn(value))
