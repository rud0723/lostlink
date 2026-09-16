import random
import string
from pathlib import Path
import qrcode

QR_DIR = Path(__file__).resolve().parent.parent / "data" / "qr_codes"
QR_DIR.mkdir(parents=True, exist_ok=True)


def generate_code() -> str:
    digits = "".join(random.choices(string.digits, k=2))
    letters = "".join(random.choices(string.ascii_uppercase, k=3))
    return f"LL-{digits}{letters}"


def generate_qr_image(code: str, base_url: str = "http://localhost:8000") -> str:
    url = f"{base_url}/item/{code}"
    img = qrcode.make(url)
    path = QR_DIR / f"{code}.png"
    img.save(path)
    return str(path)
