from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.services.notification_service import notify


def get_assets(db: Session):
    return db.query(Asset).all()


def get_asset(db: Session, asset_id: int):
    return db.query(Asset).filter(Asset.id == asset_id).first()


def _asset_fields(asset: Asset) -> list[dict]:
    return [
        {"label": "Asset", "value": asset.asset_name},
        {"label": "Asset Tag", "value": asset.asset_tag},
        {"label": "Type", "value": asset.asset_type},
        {"label": "Hostname", "value": asset.hostname or "N/A"},
    ]


def create_asset(db: Session, asset, background_tasks=None):

    db_asset = Asset(**asset.model_dump())

    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)

    notify(
        db, background_tasks,
        event_type="asset_added",
        title=f"New Asset Added: {db_asset.asset_name}",
        message=f"{db_asset.asset_name} has been added to inventory.",
        asset_id=db_asset.id,
        extra_fields=_asset_fields(db_asset),
        dashboard_path=f"/asset/{db_asset.id}",
    )

    return db_asset


def update_asset(db: Session, asset_id: int, asset, background_tasks=None):

    db_asset = get_asset(db, asset_id)

    if not db_asset:
        return None

    for key, value in asset.model_dump(exclude_unset=True).items():
        setattr(db_asset, key, value)

    db.commit()
    db.refresh(db_asset)

    notify(
        db, background_tasks,
        event_type="asset_updated",
        title=f"Asset Updated: {db_asset.asset_name}",
        message=f"{db_asset.asset_name} has been updated.",
        asset_id=db_asset.id,
        extra_fields=_asset_fields(db_asset),
        dashboard_path=f"/asset/{db_asset.id}",
    )

    return db_asset


def delete_asset(db: Session, asset_id: int, background_tasks=None):

    db_asset = get_asset(db, asset_id)

    if not db_asset:
        return None

    # Fields captured before delete -- and asset_id deliberately left
    # off the notification below, since the asset row (and its FK)
    # won't exist anymore by the time this notification is read.
    fields = _asset_fields(db_asset)
    asset_name = db_asset.asset_name

    db.delete(db_asset)
    db.commit()

    notify(
        db, background_tasks,
        event_type="asset_deleted",
        title=f"Asset Deleted: {asset_name}",
        message=f"{asset_name} has been removed from inventory.",
        extra_fields=fields,
        dashboard_path="/assets",
    )

    return True