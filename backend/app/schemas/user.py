from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    password: str
    role_id: int


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: EmailStr
    is_active: bool
    role_id: int
    created_at: datetime

    class Config:
        from_attributes = True