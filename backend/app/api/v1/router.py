"""
ThreatLens AI - API v1 Router
Aggregates all endpoint routers.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, files, analytics,
    classification, threats, alerts,
    integrations, reports,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(files.router)
api_router.include_router(analytics.router)
api_router.include_router(classification.router)
api_router.include_router(threats.router)
api_router.include_router(alerts.router)
api_router.include_router(integrations.router)
api_router.include_router(reports.router)
