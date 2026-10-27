from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.case import CasePriority, CaseStatus


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    crime_type: Optional[str] = Field(default=None, max_length=100)
    priority: CasePriority = CasePriority.medium
    # Sirf admin ke liye: case kisi aur investigator ko assign karna
    investigator_id: Optional[int] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = None
    crime_type: Optional[str] = Field(default=None, max_length=100)
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    # Sirf admin ke liye
    investigator_id: Optional[int] = None


class CaseOut(BaseModel):
    id: int
    case_number: str
    title: str
    description: Optional[str] = None
    crime_type: Optional[str] = None
    status: CaseStatus
    priority: CasePriority
    investigator_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseStats(BaseModel):
    total: int
    open: int
    in_progress: int
    under_review: int
    closed: int