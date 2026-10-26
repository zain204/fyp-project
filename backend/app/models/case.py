import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.connection import Base


class CaseStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    under_review = "under_review"
    closed = "closed"


class CasePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. CASE-2026-001
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    crime_type = Column(String(100), nullable=True)  # phishing, hacking, fraud...
    status = Column(Enum(CaseStatus), default=CaseStatus.open, nullable=False)
    priority = Column(Enum(CasePriority), default=CasePriority.medium, nullable=False)

    investigator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    investigator = relationship("User", back_populates="cases")
    evidence_items = relationship(
        "Evidence", back_populates="case", cascade="all, delete-orphan"
    )
    notes = relationship(
        "InvestigationNote", back_populates="case", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="case", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Case id={self.id} number={self.case_number} status={self.status}>"