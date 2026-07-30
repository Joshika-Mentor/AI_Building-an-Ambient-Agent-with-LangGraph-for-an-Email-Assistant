"""
ThreatLens AI — Alert API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AssignRequest(BaseModel):
    user_id: int


@router.get("/", summary="List alerts")
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List alerts with pagination, severity, and status filtering."""
    return await alert_service.list_alerts(
        db=db, page=page, page_size=page_size,
        severity=severity, status=status,
    )


@router.get("/stats", summary="Alert statistics")
async def get_alert_stats(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get alert statistics for dashboard widgets."""
    return await alert_service.get_alert_stats(db)


@router.get("/{alert_id}", summary="Get alert detail")
async def get_alert(
    alert_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific alert. Marks it as read."""
    return await alert_service.get_alert_by_id(alert_id, db)


@router.put("/{alert_id}/acknowledge", summary="Acknowledge alert")
async def acknowledge_alert(
    alert_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge an alert (new → acknowledged)."""
    return await alert_service.acknowledge_alert(alert_id, db)


@router.put("/{alert_id}/resolve", summary="Resolve alert")
async def resolve_alert(
    alert_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve an alert."""
    return await alert_service.resolve_alert(alert_id, db)


@router.put("/{alert_id}/assign", summary="Assign alert to user")
async def assign_alert(
    alert_id: int,
    body: AssignRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Assign an alert to a specific user for investigation."""
    return await alert_service.assign_alert(alert_id, body.user_id, db)
