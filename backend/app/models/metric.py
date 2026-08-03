from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)

    asset_id = Column(Integer, ForeignKey("assets.id"))

    cpu_usage = Column(Float)

    ram_usage = Column(Float)

    disk_usage = Column(Float)

    network_sent = Column(Float)

    network_received = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    asset = relationship("Asset")