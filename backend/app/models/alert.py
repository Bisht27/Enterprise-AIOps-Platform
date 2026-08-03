from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Asset Reference
    asset_id = Column(
        Integer,
        ForeignKey("assets.id"),
        nullable=False,
    )

    # Alert Details
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(String(255), nullable=False)

    # Alert Status
    status = Column(String(20), default="Open")

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    resolved_at = Column(DateTime, nullable=True)

    # When this alert last went out in a (consolidated) notification --
    # lets the monitoring state machine tell "brand new" from
    # "already notified, still open" and throttle reminders.
    last_notified_at = Column(DateTime, nullable=True)

    # Relationship
    asset = relationship(
        "Asset",
        back_populates="alerts",
    )
    tickets = relationship(
    "Ticket",
    back_populates="alert",
    cascade="all, delete-orphan",
    )