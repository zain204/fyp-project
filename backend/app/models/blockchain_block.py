from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.database.connection import Base


class BlockchainBlock(Base):
    """
    Evidence ledger ka ek block.
    evidence_id par foreign key nahi rakhi, taake evidence delete ho bhi jaye
    to ledger ka record (aur chain) salamat rahe.
    """

    __tablename__ = "blockchain_blocks"

    id = Column(Integer, primary_key=True, index=True)
    block_index = Column(Integer, unique=True, index=True, nullable=False)

    # Hash me use hota hai, is liye string me store kiya (DB round-trip me badalta nahi)
    timestamp = Column(String(40), nullable=False)

    evidence_id = Column(Integer, index=True, nullable=True)  # genesis block me None
    case_id = Column(Integer, nullable=True)
    evidence_hash = Column(String(64), nullable=True)  # file ka SHA-256

    previous_hash = Column(String(64), nullable=False)
    block_hash = Column(String(64), unique=True, nullable=False)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"<Block index={self.block_index} evidence={self.evidence_id}>"