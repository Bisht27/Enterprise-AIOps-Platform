from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password, verify_password
from app.services.notification_service import notify

FAILED_LOGIN_THRESHOLD = 3


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user):

    hashed_password = hash_password(user.password)

    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password=hashed_password,
        role_id=user.role_id,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def authenticate_user(
    db: Session,
    username: str,
    password: str,
    ip_address: str | None = None,
    background_tasks=None,
):

    user = get_user_by_username(db, username)

    if not user:
        return None

    if not verify_password(password, user.password):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        db.commit()

        if user.failed_login_count >= FAILED_LOGIN_THRESHOLD:
            notify(
                db, background_tasks,
                event_type="failed_login_attempts",
                title="Multiple Failed Login Attempts",
                message=f"{user.failed_login_count} consecutive failed login attempts for user '{user.username}'.",
                severity="Warning",
                users=[user],
                extra_fields=[
                    {"label": "Username", "value": user.username},
                    {"label": "Failed Attempts", "value": str(user.failed_login_count)},
                    {"label": "Last Attempt From", "value": ip_address or "Unknown"},
                ],
                dashboard_path="/settings",
            )
        return None

    # Successful login -- reset the failed counter and check for a
    # new source IP before overwriting it.
    is_new_device = bool(user.last_login_ip) and ip_address and user.last_login_ip != ip_address

    user.failed_login_count = 0
    if ip_address:
        user.last_login_ip = ip_address
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    if is_new_device:
        notify(
            db, background_tasks,
            event_type="login_new_device",
            title="Login from New Device",
            message=f"'{user.username}' logged in from a new IP address.",
            severity="Warning",
            users=[user],
            extra_fields=[
                {"label": "Username", "value": user.username},
                {"label": "New IP Address", "value": ip_address or "Unknown"},
                {"label": "Previous IP Address", "value": user.last_login_ip or "Unknown"},
            ],
            dashboard_path="/settings",
        )

    return user