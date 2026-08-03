from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.asset import Asset
from app.schemas.qr import QRScanRequest, QRScanResponse
from app.api.v1.qr.service import (
    build_asset_qr_url,
    generate_qr_image,
    resolve_scanned_code,
)

router = APIRouter(
    prefix="/qr",
    tags=["QR Asset Management"],
)


def _get_asset_or_404(db: Session, asset_id: int) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


# ==========================================================
# Single Asset QR Image (inline display, e.g. <img src=... />)
# ==========================================================

@router.get("/assets/{asset_id}")
def get_asset_qr_image(
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = _get_asset_or_404(db, asset_id)
    payload = build_asset_qr_url(asset)
    buffer = generate_qr_image(payload)

    return StreamingResponse(buffer, media_type="image/png")


# ==========================================================
# Single Asset QR Image (forced download)
# ==========================================================

@router.get("/assets/{asset_id}/download")
def download_asset_qr_image(
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = _get_asset_or_404(db, asset_id)
    payload = build_asset_qr_url(asset)
    buffer = generate_qr_image(payload)

    filename = f"{asset.asset_tag or asset.id}-qr.png"

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


# ==========================================================
# Raw QR payload (for debugging / client-side QR rendering)
# ==========================================================

@router.get("/assets/{asset_id}/data")
def get_asset_qr_data(
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = _get_asset_or_404(db, asset_id)
    return {"asset_id": asset.id, "url": build_asset_qr_url(asset)}


# ==========================================================
# Bulk listing — used by the frontend to render a printable
# sheet of QR codes (one <img> per asset, pointing back at
# GET /qr/assets/{asset_id}).
# ==========================================================

@router.get("/assets")
def list_assets_for_qr(
    db: Session = Depends(get_db),
) -> List[dict]:
    assets = db.query(Asset).filter(Asset.is_active == True).all()  # noqa: E712
    return [
        {
            "id": a.id,
            "asset_tag": a.asset_tag,
            "asset_name": a.asset_name,
            "asset_type": a.asset_type,
            "location": a.location,
        }
        for a in assets
    ]


# ==========================================================
# Scan Resolution — a scanned QR/barcode string comes in,
# the matching asset comes back out.
# ==========================================================

@router.post("/scan", response_model=QRScanResponse)
def scan_qr_code(
    payload: QRScanRequest,
    db: Session = Depends(get_db),
):
    asset, matched_by = resolve_scanned_code(db, payload.code)

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="No asset matches the scanned code",
        )

    return QRScanResponse(asset=asset, matched_by=matched_by)
