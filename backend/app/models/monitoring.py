from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.database.base import Base


class Monitoring(Base):
    __tablename__ = "monitoring"

    id = Column(Integer, primary_key=True, index=True)

    asset_id = Column(
        Integer,
        ForeignKey("assets.id"),
        nullable=False,
    )

    cpu_usage = Column(Float)

    ram_usage = Column(Float)

    disk_usage = Column(Float)

    network_sent = Column(Float)

    network_received = Column(Float)

    # Best-effort extras the agent attaches to each heartbeat so the
    # consolidated alert notification (see check_thresholds) can show
    # "who was logged in" / "what was running" context without a
    # separate lookup. Nullable -- older agents that haven't upgraded
    # yet simply omit these and the UI/templates show "N/A".
    logged_in_user = Column(String(150), nullable=True)
    running_processes = Column(Integer, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    asset = relationship("Asset")