from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    role: UserRole = UserRole.investigator
    badge_number: Optional[str] = Field(default=None, max_length=50)
    admin_code: Optional[str] = None  # sirf admin signup ke liye zaroori


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    badge_number: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)