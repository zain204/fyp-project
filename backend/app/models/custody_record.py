from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.connection import Base


class CustodyRecord(Base):
    """Chain of Custody: evidence ke saath kisne, kab, kya kiya."""

    __tablename__ = "custody_records"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # uploaded / viewed / downloaded / analyzed / verified / transferred
    action = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)

    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    evidence = relationship("Evidence", back_populates="custody_records")
    user = relationship("User")

    def __repr__(self):
        return f"<CustodyRecord evidence={self.evidence_id} action={self.action}>"