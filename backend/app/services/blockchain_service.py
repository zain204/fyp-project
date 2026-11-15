from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.blockchain_block import BlockchainBlock
from app.models.evidence import Evidence
from app.services.hashing import sha256_of_bytes

GENESIS_PREV_HASH = "0" * 64


@dataclass
class ChainCheck:
    is_valid: bool
    total_blocks: int
    broken_at_index: Optional[int]
    message: str


def compute_block_hash(
    block_index: int,
    timestamp: str,
    evidence_id: Optional[int],
    case_id: Optional[int],
    evidence_hash: Optional[str],
    previous_hash: str,
) -> str:
    payload = "|".join(
        [
            str(block_index),
            timestamp,
            str(evidence_id if evidence_id is not None else ""),
            str(case_id if case_id is not None else ""),
            evidence_hash or "",
            previous_hash,
        ]
    )
    return sha256_of_bytes(payload.encode("utf-8"))


def _latest_block(db: Session) -> Optional[BlockchainBlock]:
    return (
        db.query(BlockchainBlock)
        .order_by(BlockchainBlock.block_index.desc())
        .first()
    )


def ensure_genesis_block(db: Session) -> BlockchainBlock:
    """First block (index 0). Creates it if the chain is empty."""
    latest = _latest_block(db)
    if latest is not None:
        return latest

    timestamp = datetime.now(timezone.utc).isoformat()
    block = BlockchainBlock(
        block_index=0,
        timestamp=timestamp,
        evidence_id=None,
        case_id=None,
        evidence_hash="GENESIS",
        previous_hash=GENESIS_PREV_HASH,
        block_hash=compute_block_hash(
            0, timestamp, None, None, "GENESIS", GENESIS_PREV_HASH
        ),
    )
    db.add(block)
    db.flush()
    return block


def add_evidence_block(db: Session, evidence: Evidence) -> BlockchainBlock:
    """
    Adds the evidence hash to the ledger as a new block.
    evidence.id must exist (call db.flush() first). The caller commits.
    """
    latest = ensure_genesis_block(db)

    index = latest.block_index + 1
    timestamp = datetime.now(timezone.utc).isoformat()
    block_hash = compute_block_hash(
        index,
        timestamp,
        evidence.id,
        evidence.case_id,
        evidence.sha256_hash,
        latest.block_hash,
    )

    block = BlockchainBlock(
        block_index=index,
        timestamp=timestamp,
        evidence_id=evidence.id,
        case_id=evidence.case_id,
        evidence_hash=evidence.sha256_hash,
        previous_hash=latest.block_hash,
        block_hash=block_hash,
    )
    db.add(block)
    db.flush()

    evidence.blockchain_block_index = index
    return block


def get_block_for_evidence(db: Session, evidence_id: int) -> Optional[BlockchainBlock]:
    return (
        db.query(BlockchainBlock)
        .filter(BlockchainBlock.evidence_id == evidence_id)
        .order_by(BlockchainBlock.block_index.asc())
        .first()
    )


def verify_chain(db: Session) -> ChainCheck:
    """Checks the whole chain: index order, previous_hash links and each block's own hash."""
    blocks = (
        db.query(BlockchainBlock).order_by(BlockchainBlock.block_index.asc()).all()
    )

    if not blocks:
        return ChainCheck(True, 0, None, "The chain is empty")

    expected_prev = GENESIS_PREV_HASH

    for position, block in enumerate(blocks):
        if block.block_index != position:
            return ChainCheck(
                False,
                len(blocks),
                position,
                f"Block {position} is missing or its index was changed",
            )

        if block.previous_hash != expected_prev:
            return ChainCheck(
                False,
                len(blocks),
                block.block_index,
                f"The link at block {block.block_index} is broken (previous hash does not match)",
            )

        recomputed = compute_block_hash(
            block.block_index,
            block.timestamp,
            block.evidence_id,
            block.case_id,
            block.evidence_hash,
            block.previous_hash,
        )
        if recomputed != block.block_hash:
            return ChainCheck(
                False,
                len(blocks),
                block.block_index,
                f"The data in block {block.block_index} was modified (hash does not match)",
            )

        expected_prev = block.block_hash

    return ChainCheck(True, len(blocks), None, "The whole chain is valid, no tampering detected")