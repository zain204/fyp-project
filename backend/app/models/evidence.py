from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    file_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())