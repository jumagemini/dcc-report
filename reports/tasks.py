import re
import logging
from PIL import Image, ImageFilter, ImageOps
from celery import shared_task
import pytesseract

logger = logging.getLogger(__name__)

# Device‑specific length / format constraints (applied AFTER prefix extraction)
DEVICE_CONSTRAINTS = {
    'ONU': {'min_len': 14},
    'AP1': {'min_len': 10},
    'AP2': {'min_len': 10},
    'AP3': {'min_len': 10},
    'OUT': {'min_len': 10},
}

# Common location words to ignore
NOT_SERIAL = {
    'CDF', 'CORRIDOR', 'OFFICE', 'ROOM', 'LIBRARY', 'LAB',
    'STAFFROOM', 'BOARDROOM', 'RECEPTION', 'ENTRANCE', 'BLOCK',
    'ADMIN', 'PRINCIPAL', 'DEPUTY', 'ICT', 'CLASSROOM',
}

# -------------------------------
# Lightweight preprocessing
# -------------------------------
def preprocess_image(img):
    """
    Very gentle preparation:
    - Resize if the image is tiny
    - Convert to grayscale
    - Apply a light sharpening (optional)
    Returns a Pillow Image.
    """
    w, h = img.size
    # Resize only if extremely small
    if w < 800:
        ratio = 800 / w
        new_size = (800, int(h * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Convert to grayscale
    img = img.convert('L')

    # Very light sharpening – can be removed if it still garbles
    img = img.filter(ImageFilter.SHARPEN)

    return img

# -------------------------------
# Robust serial extraction
# -------------------------------
def extract_serial_from_text(raw_text, device_type):
    """
    Extract the most likely serial number for a given device type.
    """
    text = raw_text.replace('\n', ' ').replace('\r', ' ')

    # ----- Device‑specific primary prefixes -----
    primary_prefixes = {
        'ONU': [r'PON\s*SN\s*[:=]?\s*([A-Z0-9 ]+)'],   # allow spaces, will clean later
        'AP1': [r'SN\s*[:=]?\s*([A-Z0-9]+)'],
        'AP2': [r'SN\s*[:=]?\s*([A-Z0-9]+)'],
        'AP3': [r'SN\s*[:=]?\s*([A-Z0-9]+)'],
        'OUT': [r'(?:\(S\)\s*)?(?:S\/N|SN)\s*[:=]?\s*([A-Z0-9]+)'],
    }

    # Generic fallback pattern (used if primary fails)
    generic_pattern = r'(?:\(S\)\s*)?(?:S\/N|SN|PON\s*SN)\s*[:=]?\s*([A-Z0-9]+)'

    candidates = []
    for pattern in primary_prefixes.get(device_type, [generic_pattern]):
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # For ONU, remove internal spaces and concatenate the parts
            if device_type == 'ONU':
                # Join all captures (may have multiple groups if pattern had multiple ())
                # For the pattern with one capture group, matches is a list of strings
                candidates = [m.replace(' ', '') for m in matches if m.strip()]
            else:
                candidates = [m.strip() for m in matches if m.strip()]
            if candidates:
                break

    # If primary gave nothing, try the generic prefix
    if not candidates:
        matches = re.findall(generic_pattern, text, re.IGNORECASE)
        candidates = [m.strip() for m in matches if m.strip()]

    # Filter out obvious non‑serials
    candidates = [c for c in candidates if len(c) >= 8]
    # Exclude location words
    NOT_SERIAL = {
        'CDF', 'CORRIDOR', 'OFFICE', 'ROOM', 'LIBRARY', 'LAB',
        'STAFFROOM', 'BOARDROOM', 'RECEPTION', 'ENTRANCE', 'BLOCK',
        'ADMIN', 'PRINCIPAL', 'DEPUTY', 'ICT', 'CLASSROOM',
    }
    candidates = [c for c in candidates if not any(word in c.upper() for word in NOT_SERIAL)]
    # Prefer those with both letters and digits, minimum length
    candidates = [c for c in candidates if any(ch.isdigit() for ch in c) and any(ch.isalpha() for ch in c)]
    min_len = DEVICE_CONSTRAINTS.get(device_type, {}).get('min_len', 10)
    candidates = [c for c in candidates if len(c) >= min_len]

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique[:3]

# -------------------------------
# Celery task
# -------------------------------
@shared_task(bind=True, max_retries=3)
def extract_serial_numbers(self, image_path, device_type='AP1'):
    try:
        img = Image.open(image_path)

        # First pass: light preprocessing (existing code)
        img_light = preprocess_image(img)
        raw_text = pytesseract.image_to_string(img_light, config='--psm 6')
        logger.info(f"OCR raw text for {device_type} (light): {raw_text}")
        serials = extract_serial_from_text(raw_text, device_type)
        if serials:
            return serials[:3]

        # If nothing found and device is Indoor AP, try a second pass with heavier processing
        if device_type in ('AP1', 'AP2', 'AP3'):
            logger.info(f"Retrying with heavy preprocessing for {device_type}")
            img_heavy = preprocess_image_heavy(img)
            raw_text2 = pytesseract.image_to_string(img_heavy, config='--psm 6')
            logger.info(f"OCR raw text for {device_type} (heavy): {raw_text2}")
            serials2 = extract_serial_from_text(raw_text2, device_type)
            if serials2:
                return serials2[:3]

        return []

    except Exception as e:
        logger.exception("OCR task failed")
        self.retry(exc=e, countdown=10)


def preprocess_image_heavy(img):
    """
    Aggressive preprocessing for difficult images:
    - Grayscale
    - High-contrast autocontrast
    - Strong binarisation
    - Optional: adaptive threshold if OpenCV is available
    """
    img = img.convert('L')
    # Stretch contrast aggressively
    img = ImageOps.autocontrast(img, cutoff=2)
    # Binarisation with lower threshold (keep more dark pixels)
    img = img.point(lambda p: 255 if p > 110 else 0)
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)

    # Try OpenCV adaptive threshold if installed (handles uneven lighting/glossy surfaces)
    try:
        import cv2
        import numpy as np
        img_cv = np.array(img)
        img_cv = cv2.adaptiveThreshold(
            img_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        img = Image.fromarray(img_cv)
    except ImportError:
        pass   # keep the Pillow result

    return img        