"""
ThreatLens AI — Threat Monitoring API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.services import threat_service

router = APIRouter(prefix="/threats", tags=["Threats"])


class NoteRequest(BaseModel):
    notes: str


@router.get("/", summary="List threat incidents")
async def list_threats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List threat incidents with pagination and filtering."""
    return await threat_service.list_threats(
        db=db, page=page, page_size=page_size,
        severity=severity, status=status,
    )


@router.get("/stats", summary="Threat statistics")
async def get_threat_stats(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get threat incident statistics for dashboard."""
    return await threat_service.get_threat_stats(db)


@router.get("/{threat_id}", summary="Get threat detail")
async def get_threat(
    threat_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed threat incident with timeline and notes."""
    return await threat_service.get_threat_by_id(threat_id, db)


@router.put("/{threat_id}/status", summary="Update threat status")
async def update_status(
    threat_id: int,
    status_update: threat_service.ThreatStatusUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update threat incident status (open → investigating → contained → resolved)."""
    return await threat_service.update_threat_status(
        threat_id, status_update, current_user.id, db,
    )


@router.post("/{threat_id}/notes", summary="Add analyst notes")
async def add_notes(
    threat_id: int,
    body: NoteRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add analyst notes to a threat incident."""
    return await threat_service.add_threat_notes(
        threat_id, body.notes, current_user.id, db,
    )
