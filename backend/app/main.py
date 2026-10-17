
from fastapi import FastAPI
from sqlalchemy import text

from app.database.connection import engine, Base
from app.models import user, case, evidence
from app.routers.auth import router as auth_router
app = FastAPI(
    title="Forensic Investigation System",
    description="AI-Powered Crime Investigation & Forensic Evidence Management System",
    version="1.0.0"
)
app.include_router(auth_router)
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "Forensic Investigation System API is running"
    }


@app.get("/test-db")
def test_database():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "success",
            "message": "PostgreSQL connected successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
