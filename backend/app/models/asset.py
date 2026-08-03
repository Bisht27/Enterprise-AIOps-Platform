from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class Asset(Base):
    __tablename__ = "assets"

    # ==========================
    # Primary Key
    # ==========================
    id = Column(Integer, primary_key=True, index=True)

    # ==========================
    # Asset Information
    # ==========================
    asset_tag = Column(String(50), unique=True, nullable=False)
    asset_name = Column(String(150), nullable=False)
    asset_type = Column(String(50), nullable=False)

    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100), unique=True)

    # ==========================
    # Operating System
    # ==========================
    operating_system = Column(String(100))
    hostname = Column(String(100))

    # ==========================
    # Agent Identity (auto-registration)
    # ==========================
    # Generated once when an agent first registers itself; the agent
    # caches these locally and reuses them on every subsequent
    # heartbeat/registration instead of creating a new asset.
    agent_uuid = Column(String(36), unique=True, nullable=True)
    api_key = Column(String(64), unique=True, nullable=True)

    # ==========================
    # Extended Hardware / Cloud Info
    # ==========================
    # Best-effort fields the agent may or may not be able to detect
    # depending on OS/permissions/environment -- nullable, shown as
    # "Not available" in the UI when empty.
    os_version = Column(String(100), nullable=True)
    motherboard = Column(String(150), nullable=True)
    bios_version = Column(String(100), nullable=True)
    gpu = Column(String(150), nullable=True)
    cloud_provider = Column(String(50), nullable=True)
    cloud_region = Column(String(50), nullable=True)
    instance_id = Column(String(100), nullable=True)

    # ==========================
    # Network Information
    # ==========================
    ip_address = Column(String(50))
    private_ip = Column(String(100))
    public_ip = Column(String(100))
    mac_address = Column(String(50), unique=True)

    # ==========================
    # CPU Information
    # ==========================
    cpu_name = Column(String(200))
    cpu_cores = Column(Integer)
    cpu_threads = Column(Integer)

    # ==========================
    # Memory Information
    # ==========================
    ram_total = Column(String(50))

    # ==========================
    # Disk Information
    # ==========================
    disk_total = Column(String(50))
    disk_used = Column(String(50))
    disk_free = Column(String(50))

    # ==========================
    # Asset Details
    # ==========================
    location = Column(String(100))
    department = Column(String(100), nullable=True)
    status = Column(String(50), default="Available")

    assigned_to = Column(Integer, ForeignKey("users.id"))

    purchase_date = Column(DateTime)
    warranty_expiry = Column(DateTime)
    license_expiry = Column(DateTime, nullable=True)
    next_maintenance_date = Column(DateTime, nullable=True)

    # ==========================
    # Agent Monitoring
    # ==========================
    health_status = Column(String(30), default="Healthy")

    agent_version = Column(String(20))

    last_seen = Column(DateTime)

    is_online = Column(Boolean, default=False)

    # ==========================
    # Audit Fields
    # ==========================
    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    is_active = Column(Boolean, default=True)

    # ==========================
    # Relationships
    # ==========================
    monitoring = relationship(
    "Monitoring",
    back_populates="asset",
    cascade="all, delete-orphan",
    )
    alerts = relationship(
    "Alert",
    back_populates="asset",
    cascade="all, delete-orphan",
    )