import qrcode
from pathlib import Path


QR_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "qr_codes"
)

QR_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def generate_code():

    import random
    import string

    return (
        "LL-" +
        "".join(
            random.choices(
                string.ascii_uppercase +
                string.digits,
                k=5
            )
        )
    )


def generate_qr_image(
    code: str,
    base_url: str = "http://192.168.29.76:8000"
):

    url = (
        f"{base_url}/item/{code}"
    )


    img = qrcode.make(url)


    path = (
        QR_DIR /
        f"{code}.png"
    )


    img.save(path)


    return str(path)