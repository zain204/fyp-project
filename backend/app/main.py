import importlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.connection import Base, engine

logger = logging.getLogger("uvicorn.error")

# (module path, URL prefix, swagger tag)
# Jo file abhi khali hai (router nahi bana), wo automatically skip ho jayegi
ROUTER_MODULES = [
    ("app.api.auth", "/api/auth", "Authentication"),
    ("app.api.cases", "/api/cases", "Cases"),
    ("app.api.evidence", "/api/evidence", "Evidence"),
    ("app.api.analysis", "/api/analysis", "AI Analysis"),
    ("app.api.blockchain", "/api/blockchain", "Blockchain"),
    ("app.api.reports", "/api/reports", "Reports"),
]


def create_tables() -> None:
    """Saare models import karke database tables bana deta hai."""
    try:
        import app.models  # noqa: F401  (models/__init__.py me saare models import hone chahiye)
    except ImportError as e:
        logger.warning(f"Models import nahi hue: {e}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Server start hone par
    create_tables()
    yield
    # Server band hone par (abhi kuch nahi)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ---------- CORS (React frontend ko allow karne ke liye) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Routers automatically include ----------
def include_routers() -> None:
    for module_path, prefix, tag in ROUTER_MODULES:
        try:
            module = importlib.import_module(module_path)
        except Exception as e:
            logger.warning(f"Skip {module_path}: {e}")
            continue

        router = getattr(module, "router", None)
        if router is None:
            logger.warning(f"Skip {module_path}: 'router' abhi nahi bana")
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