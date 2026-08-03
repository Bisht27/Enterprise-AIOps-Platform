from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import relationship

from app.database.base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Related Alert
    alert_id = Column(
        Integer,
        ForeignKey("alerts.id"),
        nullable=False,
    )

    # Ticket Details
    title = Column(String(200), nullable=False)

    description = Column(Text)

    priority = Column(
        String(20),
        default="Medium",
    )

    status = Column(
        String(20),
        default="Open",
    )

    assigned_to = Column(
        String(100),
        nullable=True,
    )

    resolution_notes = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    alert = relationship(
        "Alert",
        back_populates="tickets",
    )