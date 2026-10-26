from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    original_filename = Column(String(255), nullable=False)  # user ne jo naam diya
    stored_filename = Column(String(255), nullable=False)    # server pe save hone wala unique naam
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=True)           # MIME type
    file_size = Column(BigInteger, nullable=True)            # bytes me
    description = Column(Text, nullable=True)

    # ---- Tamper-proof fields ----
    sha256_hash = Column(String(64), nullable=False, index=True)
    blockchain_block_index = Column(Integer, nullable=True)  # blockchain ledger me block number
    is_verified = Column(Boolean, default=True, nullable=False)  # last verification result

    uploaded_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    case = relationship("Case", back_populates="evidence_items")
    uploader = relationship("User")
    custody_records = relationship(
        "CustodyRecord", back_populates="evidence", cascade="all, delete-orphan"
    )
    ai_findings = relationship(
        "AIFinding", back_populates="evidence", cascade="all, delete-orphan"
    )
    features = relationship(
        "EvidenceFeatures",
        back_populates="evidence",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Evidence id={self.id} file={self.original_filename}>"