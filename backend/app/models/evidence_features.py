from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.database.connection import Base


class EvidenceFeatures(Base):
    """AI ke liye evidence se nikali gayi features (metadata, keywords, entropy wagera)."""

    __tablename__ = "evidence_features"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(
        Integer, ForeignKey("evidence.id"), unique=True, nullable=False, index=True
    )

    features = Column(JSON, nullable=True)        # {"entropy": 7.2, "urls": [...], ...}
    extracted_text = Column(Text, nullable=True)  # file se nikala hua text

    extracted_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    evidence = relationship("Evidence", back_populates="features")

    def __repr__(self):
        return f"<EvidenceFeatures evidence={self.evidence_id}>"