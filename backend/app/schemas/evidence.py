from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EvidenceOut(BaseModel):
    id: int
    case_id: int
    uploaded_by: int
    original_filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    description: Optional[str] = None
    sha256_hash: str
    blockchain_block_index: Optional[int] = None
    is_verified: bool
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustodyRecordOut(BaseModel):
    id: int
    evidence_id: int
    user_id: int
    action: str
    notes: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class VerifyResult(BaseModel):
    evidence_id: int
    original_hash: str
    current_hash: Optional[str] = None
    blockchain_hash: Optional[str] = None
    block_index: Optional[int] = None
    blockchain_verified: Optional[bool] = None  # None = is evidence ka block nahi hai
    chain_valid: Optional[bool] = None
    is_intact: bool
    status: str  # "intact" | "tampered" | "missing" | "ledger_broken"
    message: str
    verified_at: datetime