from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    asset_id: int
    alert_type: str
    severity: str
    message: str


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    status: str


class AlertResponse(AlertBase):
    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)