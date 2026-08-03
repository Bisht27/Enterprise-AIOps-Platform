from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TicketBase(BaseModel):
    alert_id: int
    title: str
    description: Optional[str] = None
    priority: str = "Medium"


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    # Added so priority changes (e.g. escalating to "Critical") can be
    # made through the existing update endpoint -- optional/unset by
    # default, so this doesn't affect any existing caller.
    priority: Optional[str] = None


class TicketResponse(TicketBase):
    id: int
    status: str
    assigned_to: Optional[str]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)