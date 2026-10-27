from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BlockOut(BaseModel):
    id: int
    block_index: int
    timestamp: str
    evidence_id: Optional[int] = None
    case_id: Optional[int] = None
    evidence_hash: Optional[str] = None
    previous_hash: str
    block_hash: str

    model_config = ConfigDict(from_attributes=True)


class ChainVerifyResult(BaseModel):
    is_valid: bool
    total_blocks: int
    broken_at_index: Optional[int] = None
    message: str
    checked_at: datetime