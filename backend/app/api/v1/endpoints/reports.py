"""
ThreatLens AI — Report API Endpoints
Security report generation and retrieval.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/executive-summary", summary="Executive summary report")
async def get_executive_summary(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an executive summary report.
    High-level security posture overview with health score,
    risk distribution, malware breakdown, and incident summary.
    """
    return await report_service.generate_executive_summary(db)


@router.get("/file/{file_analysis_id}", summary="File analysis report")
async def get_file_report(
    file_analysis_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a detailed report for a specific file analysis.
    Includes static analysis, ML classification, threat incidents,
    and recommended response actions.
    """
    return await report_service.generate_file_report(file_analysis_id, db)


@router.get("/threat-landscape", summary="Threat landscape report")
async def get_threat_landscape(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a threat landscape report.
    Recent detections, top threats, top malware families,
    and severity breakdown across all incidents.
    """
    return await report_service.generate_threat_landscape_report(db)
