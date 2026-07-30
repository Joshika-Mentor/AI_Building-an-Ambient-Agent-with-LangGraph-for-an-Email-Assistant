"""
ThreatLens AI - FastAPI Application
Main application factory with middleware stack and lifecycle events.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_databases, close_databases, engine, Base
from app.core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware, RequestValidationMiddleware
from app.api.v1.router import api_router

# Import all models so they're registered with Base.metadata
from app.models import User, FileAnalysis, ClassificationResult, ThreatIncident, Alert


# ─── Logging ───────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("threatlens")


# ─── Lifecycle ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("🚀 Starting ThreatLens AI...")

    # Create upload directory
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)

    # Create database tables (dev mode - use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created")

    # Initialize external connections
    try:
        await init_databases()
        logger.info("✅ MongoDB and Redis connected")
    except Exception as e:
        logger.warning(f"⚠️  Optional services not available: {e}")

    # Initialize YARA scanner
    try:
        from app.yara_rules.scanner import get_scanner
        scanner = get_scanner()
        logger.info("✅ YARA scanner initialized")
    except Exception as e:
        logger.warning(f"⚠️  YARA scanner init failed: {e}")

    # Load ML model
    try:
        from app.ml.model_repository import get_model_repository
        repo = get_model_repository()
        pipeline = repo.get_active_pipeline()
        if pipeline:
            logger.info(f"✅ ML model loaded (version: {repo.active_version})")
        else:
            logger.info("ℹ️  No trained ML model found — run 'python -m app.ml.train' to train")
    except Exception as e:
        logger.warning(f"⚠️  ML model loading failed: {e}")

    logger.info("🛡️  ThreatLens AI is ready!")

    yield

    # Shutdown
    logger.info("Shutting down ThreatLens AI...")
    try:
        await close_databases()
    except Exception:
        pass
    await engine.dispose()
    logger.info("👋 ThreatLens AI stopped.")


# ─── App Factory ───────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered malware classification and threat detection platform. "
        "Upload suspicious files for static analysis, ML-based classification, "
        "and comprehensive threat monitoring."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Middleware Stack (order matters: last added = first executed) ──

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Request validation
app.add_middleware(RequestValidationMiddleware)


# ─── Routes ────────────────────────────────────────────────────────

app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "database": "connected",
        },
    }
