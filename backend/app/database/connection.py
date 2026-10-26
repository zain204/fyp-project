from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# SQLite ko extra argument chahiye hota hai, PostgreSQL ko nahi
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Saare models (user, case, evidence...) is Base se inherit karenge
Base = declarative_base()


def get_db():
    """
    FastAPI dependency.
    Har request ke liye DB session deta hai aur kaam khatam hone par band kar deta hai.

    Use:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()