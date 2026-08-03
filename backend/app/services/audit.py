from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    target: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
) -> None:
    """
    Fire-and-forget audit trail write. Never raises -- an audit log
    failure should never break the actual request it's logging.
    """
    try:
        db.add(AuditLog(
            user_id=user_id,
            action=action,
            target=target,
            detail=detail,
            ip_address=ip_address,
        ))
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
