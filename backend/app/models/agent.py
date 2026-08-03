from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)

    hostname = Column(String(100), nullable=False)

    private_ip = Column(String(50))

    public_ip = Column(String(50))

    operating_system = Column(String(100))

    agent_version = Column(String(20))

    status = Column(String(20), default="Offline")

    last_seen = Column(DateTime(timezone=True), server_default=func.now())