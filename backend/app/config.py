from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings(BaseSettings):
    # ---------- App ----------
    APP_NAME: str = "AI-Powered Crime Investigation & Forensic Evidence Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ---------- Database ----------
    # SQLite (default):      sqlite:///./forensic.db
    # PostgreSQL (baad me):  postgresql+psycopg2://user:password@localhost:5432/forensic_db
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'forensic.db').as_posix()}"

    # ---------- Security / JWT ----------
    SECRET_KEY: str = "change-this-secret-key-in-env-file"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Admin account banane ke liye secret code
    ADMIN_SIGNUP_CODE: str = "FYP-ADMIN-2026"

    # ---------- CORS (frontend Vite default port 5173) ----------
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ---------- Evidence file storage ----------
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Upload folder automatically ban jayega
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)