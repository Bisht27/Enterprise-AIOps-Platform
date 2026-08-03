from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class AuditLog(Base):
    """
    One row per sensitive action -- who did what, when. Read via
    GET /api/v1/audit (admin only). This is intentionally a flat,
    generic log (action + target) rather than one table per module,
    so every part of the app can write to it the same way:

        from app.services.audit import log_action
        log_action(db, user_id=current_user.id, action="notification.test_email",
                    target="ops@company.com")
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    target = Column(String(200), nullable=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")
