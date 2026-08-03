from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.alert import AlertCreate, AlertResponse

from app.api.v1.alerts.service import (
    create_alert,
    get_all_alerts,
    get_alert,
    resolve_alert,
    delete_alert,
)

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.post(
    "/",
    response_model=AlertResponse,
)
def create_new_alert(
    data: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    return create_alert(db, data, background_tasks)


@router.get(
    "/",
    response_model=list[AlertResponse],
)
def list_alerts(
    db: Session = Depends(get_db),
):
    return get_all_alerts(db)


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
)
def get_single_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = get_alert(db, alert_id)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert


@router.put(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
)
def resolve_single_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = resolve_alert(db, alert_id)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert


@router.delete(
    "/{alert_id}",
)
def remove_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_alert(db, alert_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return {
        "message": "Alert deleted successfully"
    }