from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AssetBase(BaseModel):
    asset_tag: str
    asset_name: str
    asset_type: str

    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None

    operating_system: Optional[str] = None
    hostname: Optional[str] = None

    ip_address: Optional[str] = None
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None
    mac_address: Optional[str] = None

    cpu_name: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None

    ram_total: Optional[str] = None

    disk_total: Optional[str] = None
    disk_used: Optional[str] = None
    disk_free: Optional[str] = None

    location: Optional[str] = None
    department: Optional[str] = None
    assigned_to: Optional[int] = None

    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    license_expiry: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None

    health_status: Optional[str] = "Healthy"
    status: Optional[str] = "Available"

    agent_version: Optional[str] = None
    is_online: Optional[bool] = False


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    asset_name: Optional[str] = None

    manufacturer: Optional[str] = None
    model: Optional[str] = None

    operating_system: Optional[str] = None

    ip_address: Optional[str] = None
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None

    location: Optional[str] = None
    department: Optional[str] = None

    assigned_to: Optional[int] = None

    status: Optional[str] = None
    health_status: Optional[str] = None

    warranty_expiry: Optional[datetime] = None
    license_expiry: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None

    is_online: Optional[bool] = None

    cpu_name: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None

    ram_total: Optional[str] = None

    disk_total: Optional[str] = None
    disk_used: Optional[str] = None
    disk_free: Optional[str] = None

    last_seen: Optional[datetime] = None


class AssetResponse(AssetBase):
    id: int

    created_at: datetime
    updated_at: datetime

    last_seen: Optional[datetime] = None

    is_active: bool

    # Populated (when available) from the linked User for display on the
    # Asset Details / QR scan page. Not a column on Asset itself.
    assigned_user_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)