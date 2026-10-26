from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.connection import Base


class AIFinding(Base):
    """AI analysis ka nateeja, jese: 'Phishing email, 91% confidence'."""

    __tablename__ = "ai_findings"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False, index=True)

    finding_type = Column(String(100), nullable=False)    # phishing, malware, anomaly, keyword...
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)  # 0.0 se 1.0
    severity = Column(String(20), default="low", nullable=False)  # low / medium / high / critical

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    evidence = relationship("Evidence", back_populates="ai_findings")

    def __repr__(self):
        return f"<AIFinding type={self.finding_type} score={self.confidence_score}>"