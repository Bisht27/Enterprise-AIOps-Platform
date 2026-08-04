import secrets
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.schemas.agent import (
    AgentRegister,
    AgentCreate,
    AgentUpdate,
)
from app.services.notification_service import notify


def _apply_hardware_fields(asset: Asset, agent: AgentRegister) -> None:
    """Shared field mapping for both create and update registration paths."""
    asset.hostname = agent.hostname

    asset.cpu_name = agent.cpu_name
    asset.cpu_cores = agent.cpu_cores
    asset.cpu_threads = agent.cpu_threads

    asset.ram_total = agent.ram_total

    asset.disk_total = agent.disk_total
    asset.disk_used = agent.disk_used
    asset.disk_free = agent.disk_free

    asset.operating_system = agent.os_name
    asset.os_version = agent.os_version

    asset.private_ip = agent.private_ip
    asset.public_ip = agent.public_ip

    asset.serial_number = agent.serial_number or asset.serial_number
    asset.motherboard = agent.motherboard
    asset.bios_version = agent.bios_version
    asset.gpu = agent.gpu

    asset.cloud_provider = agent.cloud_provider
    asset.cloud_region = agent.cloud_region
    asset.instance_id = agent.instance_id

    asset.agent_version = agent.agent_version


# ===========================================================
# Register Agent (Heartbeat)
# ===========================================================

def register_agent(db: Session, agent: AgentRegister, background_tasks=None):
    """
    Register a new agent or update an existing one.

    Matches a returning agent by its cached agent_uuid first (stable
    even if the MAC address changes -- e.g. a VM moved to a different
    NIC/network), falling back to MAC address for agents that haven't
    registered since agent_uuid was introduced.
    """

    asset = None

    if agent.agent_uuid:
        asset = (
            db.query(Asset)
            .filter(Asset.agent_uuid == agent.agent_uuid)
            .first()
        )

    if not asset and agent.mac_address:
        asset = (
            db.query(Asset)
            .filter(Asset.mac_address == agent.mac_address)
            .first()
        )

    if asset:
        _apply_hardware_fields(asset, agent)

        asset.mac_address = agent.mac_address or asset.mac_address

        was_offline = asset.is_online is False
        asset.last_seen = datetime.utcnow()
        asset.is_online = True

        db.commit()
        db.refresh(asset)

        if was_offline:
            notify(
                db, background_tasks,
                event_type="server_online",
                title=f"Server Online Again: {asset.asset_name}",
                message=f"{asset.asset_name} has reconnected and is back online.",
                severity="Info",
                asset_id=asset.id,
                extra_fields=[
                    {"label": "Asset", "value": asset.asset_name},
                    {"label": "Hostname", "value": asset.hostname or "N/A"},
                ],
                dashboard_path=f"/asset/{asset.id}",
            )

        return asset

    asset = Asset(
    asset_tag=f"PC-{secrets.token_hex(4).upper()}",
    asset_name=agent.hostname,
    asset_type="Computer",

    hostname=agent.hostname,

    mac_address=agent.mac_address,

    agent_uuid=agent.agent_uuid or str(uuid.uuid4()),
    api_key=secrets.token_hex(32),

    health_status="Healthy",
    status="Available",

    last_seen=datetime.utcnow(),
    is_online=True,
)

    _apply_hardware_fields(asset, agent)

    db.add(asset)
    db.commit()
    db.refresh(asset)

    notify(
        db, background_tasks,
        event_type="agent_registered",
        title=f"Agent Registered: {asset.asset_name}",
        message=f"A new agent has registered from {asset.hostname or asset.asset_name}.",
        asset_id=asset.id,
        extra_fields=[
            {"label": "Asset", "value": asset.asset_name},
            {"label": "Hostname", "value": asset.hostname or "N/A"},
            {"label": "OS", "value": asset.operating_system or "N/A"},
            {"label": "Agent Version", "value": asset.agent_version or "N/A"},
        ],
        dashboard_path=f"/asset/{asset.id}",
    )

    return asset


# ===========================================================
# Get All Agents
# ===========================================================

def get_agents(db: Session):
    return (
        db.query(Asset)
        .order_by(Asset.hostname)
        .all()
    )


# ===========================================================
# Get Single Agent
# ===========================================================

def get_agent(db: Session, asset_id: int):
    return (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )


# ===========================================================
# Create Agent
# ===========================================================

def create_agent(
    db: Session,
    agent: AgentCreate,
):
    asset = Asset(
        asset_tag=f"PC-{agent.hostname}",
        asset_name=agent.hostname,
        asset_type="Computer",

        hostname=agent.hostname,

        private_ip=agent.private_ip,
        public_ip=agent.public_ip,

        operating_system=agent.os_name,

        cpu_name=agent.cpu_name,
        cpu_cores=agent.cpu_cores,
        cpu_threads=agent.cpu_threads,

        ram_total=agent.ram_total,

        disk_total=agent.disk_total,
        disk_used=agent.disk_used,
        disk_free=agent.disk_free,

        mac_address=agent.mac_address,

        agent_version=agent.agent_version,

        health_status="Healthy",
        status="Available",

        last_seen=datetime.utcnow(),
        is_online=True,
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


# ===========================================================
# Update Agent
# ===========================================================

def update_agent(
    db: Session,
    asset_id: int,
    agent: AgentUpdate,
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        return None

    update_data = agent.model_dump(exclude_unset=True)

    for key, value in update_data.items():

        if key == "os_name":
            setattr(asset, "operating_system", value)
        else:
            setattr(asset, key, value)

    asset.last_seen = datetime.utcnow()

    db.commit()
    db.refresh(asset)

    return asset


# ===========================================================
# Delete Agent
# ===========================================================

def delete_agent(
    db: Session,
    asset_id: int,
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        return False

    db.delete(asset)
    db.commit()

    return True