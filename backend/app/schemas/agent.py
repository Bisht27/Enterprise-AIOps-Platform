from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# -----------------------------
# Base Schema
# -----------------------------
class AgentBase(BaseModel):
    hostname: str

    private_ip: Optional[str] = None
    public_ip: Optional[str] = None

    mac_address: Optional[str] = None

    os_name: Optional[str] = None
    os_version: Optional[str] = None

    cpu_name: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None

    ram_total: Optional[str] = None

    disk_total: Optional[str] = None
    disk_used: Optional[str] = None
    disk_free: Optional[str] = None

    serial_number: Optional[str] = None
    motherboard: Optional[str] = None
    bios_version: Optional[str] = None
    gpu: Optional[str] = None

    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None
    instance_id: Optional[str] = None

    agent_version: Optional[str] = "1.0.0"

    # Sent back by the agent on every registration after the first one,
    # so the backend can recognize a returning agent even if its MAC
    # address changes (e.g. a VM re-attached to a different NIC).
    agent_uuid: Optional[str] = None


# -----------------------------
# Agent Registration
# -----------------------------
class AgentRegister(AgentBase):
    pass


# -----------------------------
# Agent Registration Response
# -----------------------------
class AgentRegisterResponse(BaseModel):
    message: str
    asset_id: int
    hostname: str
    agent_uuid: str
    api_key: str


# -----------------------------
# Create Agent
# -----------------------------
class AgentCreate(AgentBase):
    pass


# -----------------------------
# Update Agent
# -----------------------------
class AgentUpdate(BaseModel):
    hostname: Optional[str] = None

    private_ip: Optional[str] = None
    public_ip: Optional[str] = None

    mac_address: Optional[str] = None

    os_name: Optional[str] = None
    os_version: Optional[str] = None

    cpu_name: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None

    ram_total: Optional[str] = None

    disk_total: Optional[str] = None
    disk_used: Optional[str] = None
    disk_free: Optional[str] = None

    serial_number: Optional[str] = None
    motherboard: Optional[str] = None
    bios_version: Optional[str] = None
    gpu: Optional[str] = None

    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None
    instance_id: Optional[str] = None

    status: Optional[str] = None

    agent_version: Optional[str] = None


# -----------------------------
# Agent Response
# -----------------------------
class AgentResponse(AgentBase):
    id: int

    status: str

    last_seen: datetime

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    # Never echo the API key back out in general list/get responses --
    # only AgentRegisterResponse (returned once, at registration time)
    # carries it.
    model_config = ConfigDict(from_attributes=True)
