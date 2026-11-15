from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)


class ReportOut(BaseModel):
    id: int
    case_id: int
    generated_by: int
    title: str
    summary: Optional[str] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)