from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.asset import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
)
from app.api.v1.assets.service import (
    create_asset,
    delete_asset,
    get_asset,
    get_assets,
    update_asset,
)

router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)


@router.get("", response_model=List[AssetResponse])
def list_assets(
    db: Session = Depends(get_db),
):
    return get_assets(db)


@router.post("", response_model=AssetResponse)
def add_asset(
    asset: AssetCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    return create_asset(db, asset, background_tasks)


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset_by_id(
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = get_asset(db, asset_id)

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    # Not a column on Asset -- resolved here so AssetDetails / the QR scan
    # page can show a human name instead of a raw user id.
    asset.assigned_user_name = None
    if asset.assigned_to:
        user = db.query(User).filter(User.id == asset.assigned_to).first()
        if user:
            asset.assigned_user_name = user.full_name

    return asset


@router.put("/{asset_id}", response_model=AssetResponse)
def edit_asset(
    asset_id: int,
    asset: AssetUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    updated = update_asset(db, asset_id, asset, background_tasks)

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return updated


@router.delete("/{asset_id}")
def remove_asset(
    asset_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    deleted = delete_asset(db, asset_id, background_tasks)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return {"message": "Asset deleted successfully"}