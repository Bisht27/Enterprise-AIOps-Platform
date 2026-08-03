from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    UnreadCountResponse,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    DeliveryResponse,
    TestEmailRequest,
    TestWhatsAppRequest,
    TestSlackRequest,
    TestTeamsRequest,
    TestSmsRequest,
)
from app.api.v1.notifications.service import (
    list_notifications,
    get_unread_count,
    mark_as_read,
    get_delivery_history,
    retry_delivery,
    get_preferences,
    update_preferences,
    send_test_email,
    send_test_whatsapp,
    send_test_slack,
    send_test_teams,
    send_test_sms,
)
from app.services.audit import log_action

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("/", response_model=list[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_notifications(db, current_user.id)


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"unread_count": get_unread_count(db, current_user.id)}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = mark_as_read(db, current_user.id, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.get("/history", response_model=list[DeliveryResponse])
def notification_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_delivery_history(db, current_user.id)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def put_preferences(
    data: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_preferences(db, current_user.id, data)


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def read_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_preferences(db, current_user.id)


@router.post("/retry")
def retry_notification_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delivery = retry_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    log_action(db, current_user.id, "notification.retry", target=str(delivery_id))
    return delivery


@router.post("/test/email")
def test_email(
    data: TestEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = send_test_email(data.to_email)
    log_action(db, current_user.id, "notification.test_email", target=data.to_email, detail=result.get("status"))
    if result.get("status") == "Failed":
        raise HTTPException(status_code=502, detail=result.get("error"))
    return {"message": "Test email sent", "detail": result}


@router.post("/test/whatsapp")
def test_whatsapp(
    data: TestWhatsAppRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = send_test_whatsapp(data.to_number)
    log_action(db, current_user.id, "notification.test_whatsapp", target=data.to_number, detail=result.get("status"))
    if result.get("status") == "Failed":
        raise HTTPException(status_code=502, detail=result.get("error"))
    return {"message": "Test WhatsApp message sent", "detail": result}


@router.post("/test/slack")
def test_slack(
    data: TestSlackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = send_test_slack(data.webhook_url)
    log_action(db, current_user.id, "notification.test_slack", detail=result.get("status"))
    if result.get("status") == "Failed":
        raise HTTPException(status_code=502, detail=result.get("error"))
    return {"message": "Test Slack message sent", "detail": result}


@router.post("/test/teams")
def test_teams(
    data: TestTeamsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = send_test_teams(data.webhook_url)
    log_action(db, current_user.id, "notification.test_teams", detail=result.get("status"))
    if result.get("status") == "Failed":
        raise HTTPException(status_code=502, detail=result.get("error"))
    return {"message": "Test Teams message sent", "detail": result}


@router.post("/test/sms")
def test_sms(
    data: TestSmsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = send_test_sms(data.to_number)
    log_action(db, current_user.id, "notification.test_sms", target=data.to_number, detail=result.get("status"))
    if result.get("status") == "Failed":
        raise HTTPException(status_code=502, detail=result.get("error"))
    return {"message": "Test SMS sent", "detail": result}
