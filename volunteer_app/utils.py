import hmac
import hashlib
import base64
import time
from django.conf import settings
from PIL import Image
from pyzbar import pyzbar
import io


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


# -------------------- CHECK-IN / CHECK-OUT TOKEN FUNCTIONS --------------------

def make_checkin_token(activity_id: int, expires_in: int = 300) -> str:
    """Create a signed token for check-in.
    
    Format (base64 urlsafe): "CHECKIN:{activity_id}:{expiry_ts}:{sig_hex}" encoded
    expires_in: default 5 minutes (300 seconds)
    """
    ts = int(time.time()) + int(expires_in)
    payload = f"CHECKIN:{activity_id}:{ts}"
    sig = hmac.new(settings.QR_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()
    return token


def make_checkout_token(activity_id: int, expires_in: int = 300) -> str:
    """Create a signed token for check-out.
    
    Format (base64 urlsafe): "CHECKOUT:{activity_id}:{expiry_ts}:{sig_hex}" encoded
    expires_in: default 5 minutes (300 seconds)
    """
    ts = int(time.time()) + int(expires_in)
    payload = f"CHECKOUT:{activity_id}:{ts}"
    sig = hmac.new(settings.QR_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()
    return token


def verify_checkin_token(token: str):
    """Verify check-in token and return (True, activity_id) or (False, None)."""
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        parts = raw.split(":")
        if len(parts) != 4 or parts[0] != "CHECKIN":
            return False, None
        activity_id = int(parts[1])
        ts = int(parts[2])
        sig = parts[3]
        if ts < int(time.time()):
            return False, None
        payload = f"CHECKIN:{activity_id}:{ts}"
        expected = hmac.new(settings.QR_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return (hmac.compare_digest(expected, sig), activity_id) if hmac.compare_digest(expected, sig) else (False, None)
    except Exception:
        return False, None


def verify_checkout_token(token: str):
    """Verify check-out token and return (True, activity_id) or (False, None)."""
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        parts = raw.split(":")
        if len(parts) != 4 or parts[0] != "CHECKOUT":
            return False, None
        activity_id = int(parts[1])
        ts = int(parts[2])
        sig = parts[3]
        if ts < int(time.time()):
            return False, None
        payload = f"CHECKOUT:{activity_id}:{ts}"
        expected = hmac.new(settings.QR_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return (hmac.compare_digest(expected, sig), activity_id) if hmac.compare_digest(expected, sig) else (False, None)
    except Exception:
        return False, None


# -------------------- QR CODE IMAGE READING --------------------

def read_qr_code_from_image(image_file):
    """Read QR code from uploaded image file.
    
    Args:
        image_file: Django UploadedFile or file-like object
        
    Returns:
        tuple: (success: bool, qr_data: str or None, error_message: str or None)
    """
    try:
        # Read image file
        if hasattr(image_file, 'read'):
            image_data = image_file.read()
        else:
            image_data = image_file
        
        # Open image with PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (pyzbar requires RGB)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Decode QR code using pyzbar
        qr_codes = pyzbar.decode(image)
        
        if not qr_codes:
            return False, None, "ไม่พบ QR code ในรูปภาพ กรุณาตรวจสอบว่า QR code ชัดเจนและอยู่ในรูปภาพ"
        
        # Get the first QR code data
        qr_data = qr_codes[0].data.decode('utf-8')
        
        return True, qr_data, None
        
    except Exception as e:
        return False, None, f"เกิดข้อผิดพลาดในการอ่าน QR code: {str(e)}"