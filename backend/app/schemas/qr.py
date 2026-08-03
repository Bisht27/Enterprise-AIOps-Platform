from pydantic import BaseModel

from app.schemas.asset import AssetResponse


class QRScanRequest(BaseModel):
    # Raw string decoded from a scanned QR code (JSON payload produced by
    # the /qr/assets/{asset_id} endpoint, or a bare asset tag / numeric id).
    code: str


class QRScanResponse(BaseModel):
    asset: AssetResponse
    matched_by: str  # "asset_id" | "asset_tag" | "serial_number"
