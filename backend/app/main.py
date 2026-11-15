import importlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.connection import Base, engine

logger = logging.getLogger("uvicorn.error")

# (module path, URL prefix, swagger tag)
# A module that does not define a router yet is skipped automatically
ROUTER_MODULES = [
    ("app.api.auth", "/api/auth", "Authentication"),
    ("app.api.cases", "/api/cases", "Cases"),
    ("app.api.evidence", "/api/evidence", "Evidence"),
    ("app.api.analysis", "/api/analysis", "AI Analysis"),
    ("app.api.blockchain", "/api/blockchain", "Blockchain"),
    ("app.api.notes", "/api/notes", "Investigation Notes"),
    ("app.api.reports", "/api/reports", "Reports"),
]


def create_tables() -> None:
    """Imports all models and creates the database tables."""
    try:
        import app.models  # noqa: F401  (models/__init__.py must import every model)
    except ImportError as e:
        logger.warning(f"Models could not be imported: {e}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on server startup
    create_tables()
    yield
    # Runs on server shutdown (nothing to do yet)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ---------- CORS (allows the React frontend to call the API) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Automatically include routers ----------
def include_routers() -> None:
    for module_path, prefix, tag in ROUTER_MODULES:
        try:
            module = importlib.import_module(module_path)
        except Exception as e:
            logger.warning(f"Skipping {module_path}: {e}")
            continue

        router = getattr(module, "router", None)
        if router is None:
            logger.warning(f"Skipping {module_path}: no router defined yet")
            continue

        app.include_router(router, prefix=prefix, tags=[tag])
        logger.info(f"Router loaded: {module_path} -> {prefix}")


include_routers()


# ---------- Basic endpoints ----------
@app.get("/", tags=["Root"])
def root():
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "ok"}