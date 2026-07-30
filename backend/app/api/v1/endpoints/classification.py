"""
ThreatLens AI — Classification API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user, permission_required
from app.services import classification_service

router = APIRouter(prefix="/classifications", tags=["Classifications"])


@router.post("/{file_analysis_id}", summary="Classify a file using ML")
async def classify_file(
    file_analysis_id: int,
    current_user=Depends(permission_required("run_analysis")),
    db: AsyncSession = Depends(get_db),
):
    """
    Run ML-based malware classification on a previously analyzed file.

    Triggers the full pipeline:
    1. Feature extraction from static analysis
    2. ML model inference
    3. Confidence scoring
    4. Auto-incident creation for high-risk detections
    """
    return await classification_service.classify_file(
        file_analysis_id=file_analysis_id,
        user_id=current_user.id,
        db=db,
    )


@router.get("/", summary="List all classifications")
async def list_classifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    malware_class: Optional[str] = Query(None, description="Filter by malware class"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List classification results with pagination and optional filtering."""
    return await classification_service.list_classifications(
        db=db,
        page=page,
        page_size=page_size,
        malware_class=malware_class,
    )


@router.get("/stats", summary="Classification statistics")
async def get_classification_stats(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get malware classification statistics for analytics."""
    return await classification_service.get_classification_stats(db)


@router.get("/{classification_id}", summary="Get classification detail")
async def get_classification(
    classification_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific classification result by ID."""
    return await classification_service.get_classification_by_id(classification_id, db)


@router.get("/file/{file_analysis_id}", summary="Get classification for a file")
async def get_file_classification(
    file_analysis_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest classification result for a specific file analysis."""
    result = await classification_service.get_classification_by_file(file_analysis_id, db)
    if result is None:
        return {"message": "No classification found for this file. Run classification first."}
    return result
