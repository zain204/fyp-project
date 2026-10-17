from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    case_number = Column(String(50), unique=True, index=True, nullable=False)
    crime_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="open", nullable=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())