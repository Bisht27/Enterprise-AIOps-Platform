import io
import json
import re

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.asset import Asset


# A scanned string is treated as a QR-encoded asset URL if it looks like
# ".../asset/<id>" -- this is what every QR code we generate now contains,
# and what a phone camera / Google Lens will open directly in the browser.
_ASSET_URL_PATTERN = re.compile(r"/asset/(\d+)/?$")


def build_asset_qr_url(asset: Asset) -> str:
    """
    Build the real, scannable URL encoded into an asset's QR code.

    Deliberately a plain URL (not JSON) so that any stock camera app
    (Google Lens, iOS Camera, Android Camera) recognizes it and offers to
    open it in the browser with no custom scanner required.
    """
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}/asset/{asset.id}"


# Backward-compatible alias in case anything else in the codebase still
# imports the old name.
build_asset_qr_payload = build_asset_qr_url


def generate_qr_image(data: str) -> io.BytesIO:
    """
    Render `data` as a PNG QR code and return it as an in-memory buffer.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def resolve_scanned_code(db: Session, code: str):
    """
    Given a raw scanned string, try to resolve it to an Asset.

    Supports (in order):
      1. The URL produced by build_asset_qr_url(), e.g.
         http://localhost:5173/asset/15
      2. The old JSON payload produced by the previous version of this
         module ({"type": "aiops_asset", "asset_id": ...}), so QR stickers
         printed before this change keep working
      3. A bare numeric asset id
      4. A bare asset tag
      5. A bare serial number

    Returns (asset, matched_by) or (None, None).
    """
    code = code.strip()

    # 1. URL payload (current QR format)
    if code.startswith("http://") or code.startswith("https://") or "/asset/" in code:
        match = _ASSET_URL_PATTERN.search(code)
        if match:
            asset = db.query(Asset).filter(Asset.id == int(match.group(1))).first()
            if asset:
                return asset, "asset_id"

    # 2. Legacy JSON payload
    try:
        parsed = json.loads(code)
        if isinstance(parsed, dict) and "asset_id" in parsed:
            asset = (
                db.query(Asset)
                .filter(Asset.id == parsed["asset_id"])
                .first()
            )
            if asset:
                return asset, "asset_id"

            if parsed.get("asset_tag"):
                asset = (
                    db.query(Asset)
                    .filter(Asset.asset_tag == parsed["asset_tag"])
                    .first()
                )
                if asset:
                    return asset, "asset_tag"
    except (json.JSONDecodeError, TypeError):
        pass

    # 3. Bare numeric id
    if code.isdigit():
        asset = db.query(Asset).filter(Asset.id == int(code)).first()
        if asset:
            return asset, "asset_id"

    # 4. Bare asset tag
    asset = db.query(Asset).filter(Asset.asset_tag == code).first()
    if asset:
        return asset, "asset_tag"

    # 5. Bare serial number
    asset = db.query(Asset).filter(Asset.serial_number == code).first()
    if asset:
        return asset, "serial_number"

    return None, None
