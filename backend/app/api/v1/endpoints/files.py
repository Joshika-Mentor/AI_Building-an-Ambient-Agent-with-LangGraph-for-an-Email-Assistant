"""
ThreatLens AI - File Upload & Analysis Endpoints
"""

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, permission_required
from app.schemas.file import FileUploadResponse, FileAnalysisResponse, FileListResponse
from app.services.file_service import upload_and_analyze, get_analysis_by_id, list_analyses
from app.models.user import User

router = APIRouter(prefix="/files", tags=["File Analysis"])


@router.post("/upload", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(..., description="Suspicious file to analyze"),
    current_user: User = Depends(permission_required("upload_files")),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a suspicious file for static analysis.

    The system will:
    1. Validate and store the file securely
    2. Compute MD5 and SHA-256 hashes
    3. Detect file type via magic bytes
    4. Perform PE header analysis (for executables)
    5. Extract suspicious strings, URLs, and IPs
    6. Analyze API imports for malicious patterns
    7. Run YARA rule matching
    8. Calculate risk score (0-100)
    """
    return await upload_and_analyze(file, current_user.id, db)


@router.get("/{analysis_id}", response_model=FileAnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed analysis results for a specific file."""
    return await get_analysis_by_id(analysis_id, db)


@router.get("/", response_model=FileListResponse)
async def list_file_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None, description="Filter by status: pending, analyzing, completed, failed"),
    risk_level: str = Query(None, description="Filter by risk level: Critical, High, Medium, Low, Clean"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all file analyses with optional filtering."""
    return await list_analyses(db, page, page_size, status, risk_level)
