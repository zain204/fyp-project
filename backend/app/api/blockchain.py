from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.evidence import _get_evidence_for_user
from app.database.connection import get_db
from app.models.blockchain_block import BlockchainBlock
from app.models.user import User
from app.schemas.blockchain import BlockOut, ChainVerifyResult
from app.services.blockchain_service import get_block_for_evidence, verify_chain

router = APIRouter()


@router.get("/chain", response_model=List[BlockOut])
def list_chain(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full ledger (contains only ids and hashes, no sensitive data)."""
    return (
        db.query(BlockchainBlock)
        .order_by(BlockchainBlock.block_index.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/verify", response_model=ChainVerifyResult)
def verify_whole_chain(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Checks the integrity of the whole chain."""
    result = verify_chain(db)
    return ChainVerifyResult(
        is_valid=result.is_valid,
        total_blocks=result.total_blocks,
        broken_at_index=result.broken_at_index,
        message=result.message,
        checked_at=datetime.now(timezone.utc),
    )


@router.get("/evidence/{evidence_id}", response_model=BlockOut)
def get_evidence_block(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the block of a given evidence item (with access check)."""
    evidence = _get_evidence_for_user(db, evidence_id, current_user)
    block = get_block_for_evidence(db, evidence.id)
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No blockchain record exists for this evidence",
        )
    return block