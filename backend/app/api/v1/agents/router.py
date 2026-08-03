from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db

from app.schemas.agent import (
    AgentRegister,
    AgentRegisterResponse,
    AgentCreate,
    AgentUpdate,
    AgentResponse,
)

from app.api.v1.agents.service import (
    register_agent,
    get_agents,
    get_agent,
    create_agent,
    update_agent,
    delete_agent,
)

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


# ==========================================================
# Agent Registration (Heartbeat)
# ==========================================================

@router.post("/register", response_model=AgentRegisterResponse)
def register(
    agent: AgentRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    asset = register_agent(db, agent, background_tasks)

    return {
        "message": "Agent registered successfully",
        "asset_id": asset.id,
        "hostname": asset.hostname,
        "agent_uuid": asset.agent_uuid,
        "api_key": asset.api_key,
    }


# ==========================================================
# Get All Agents
# ==========================================================

@router.get("", response_model=List[AgentResponse])
def list_agents(
    db: Session = Depends(get_db),
):
    return get_agents(db)


# ==========================================================
# Create Agent
# ==========================================================

@router.post("", response_model=AgentResponse)
def add_agent(
    agent: AgentCreate,
    db: Session = Depends(get_db),
):
    return create_agent(db, agent)


# ==========================================================
# Get Agent By ID
# ==========================================================

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent_by_id(
    agent_id: int,
    db: Session = Depends(get_db),
):
    agent = get_agent(db, agent_id)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return agent


# ==========================================================
# Update Agent
# ==========================================================

@router.put("/{agent_id}", response_model=AgentResponse)
def edit_agent(
    agent_id: int,
    agent: AgentUpdate,
    db: Session = Depends(get_db),
):
    updated = update_agent(db, agent_id, agent)

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return updated


# ==========================================================
# Delete Agent
# ==========================================================

@router.delete("/{agent_id}")
def remove_agent(
    agent_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_agent(db, agent_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return {
        "message": "Agent deleted successfully"
    }