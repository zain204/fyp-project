from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.connection import Base


class AuditLog(Base):
    """System ki har important activity ka record (login, upload, delete...)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # login fail me user nahi hota

    action = Column(String(100), nullable=False)          # LOGIN, UPLOAD_EVIDENCE, CREATE_CASE...
    resource_type = Column(String(50), nullable=True)     # case, evidence, report
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)

    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog action={self.action} user={self.user_id}>"