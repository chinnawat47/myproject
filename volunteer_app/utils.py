import hmac
import hashlib
import base64
import time
from django.conf import settings


def make_qr_token(activity_id: int, expires_in: int = 900) -> str:
    """Create a short signed token for an activity.

    Format (base64 urlsafe): "{activity_id}:{expiry_ts}:{sig_hex}" encoded
    """
    ts = int(time.time()) + int(expires_in)
    payload = f"{activity_id}:{ts}"
    sig = hmac.new(settings.QR_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()
    return token


def verify_qr_token(token: str):
    """Verify token and return (True, activity_id) or (False, None)."""
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        parts = raw.split(":")
        if len(parts) != 3:
            return False, None
        activity_id = int(parts[0])
        ts = int(parts[1])
        sig = parts[2]
        if ts < int(time.time()):
            return False, None
        payload = f"{activity_id}:{ts}"
        expected = hmac.new(settings.QR_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return (hmac.compare_digest(expected, sig), activity_id) if hmac.compare_digest(expected, sig) else (False, None)
    except Exception:
        return False, None
