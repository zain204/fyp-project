from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Note content cannot be empty")
        return value


class NoteUpdate(NoteCreate):
    pass


class NoteOut(BaseModel):
    id: int
    case_id: int
    author_id: int
    author_name: str
    content: str
    created_at: datetime