from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)  # generate hui PDF ka path

    generated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    case = relationship("Case", back_populates="reports")
    generator = relationship("User")

    def __repr__(self):
        return f"<Report id={self.id} case={self.case_id}>"