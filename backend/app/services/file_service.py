"""
ThreatLens AI - File Service
FILE SERVICE (Architecture Diagram): File Upload, File Storage, File Validation, Hashing.
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import HTTPException, UploadFile

from app.models.file_analysis import FileAnalysis, AnalysisStatus
from app.schemas.file import FileUploadResponse, FileAnalysisResponse, FileListResponse, StaticAnalysisResult
from app.utils.file_utils import compute_hashes, detect_file_type, save_upload
from app.services.analysis_service import perform_full_analysis
from app.core.config import settings

logger = logging.getLogger("threatlens.file_service")


async def upload_and_analyze(
    file: UploadFile,
    user_id: int,
    db: AsyncSession,
) -> FileUploadResponse:
    """
    Upload a file, run static analysis, and return results.
    Implements the full File Service pipeline from the architecture diagram.
    """
    # 1. Validate file
    if file.size and file.size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext and settings.allowed_extensions_list and ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    # 2. Read file content
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty",
        )

    # 3. Save to storage
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), settings.UPLOAD_DIR)
    uuid_filename, storage_path = await save_upload(upload_dir, content, file.filename or "unknown")

    # 4. Compute hashes
    md5_hash, sha256_hash = await compute_hashes(storage_path)

    # 5. Detect file type
    file_type, mime_type = detect_file_type(storage_path)

    # 6. Create DB record
    analysis = FileAnalysis(
        filename=uuid_filename,
        original_name=file.filename or "unknown",
        file_size=file_size,
        file_type=file_type,
        mime_type=mime_type,
        md5_hash=md5_hash,
        sha256_hash=sha256_hash,
        storage_path=storage_path,
        status=AnalysisStatus.ANALYZING.value,
        uploaded_by=user_id,
    )
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)

    # 7. Run static analysis
    try:
        results = await perform_full_analysis(storage_path)

        # Update analysis record with results
        analysis.status = AnalysisStatus.COMPLETED.value
        analysis.risk_score = results["risk_score"]
        analysis.risk_level = results["risk_level"]
        analysis.pe_info = json.dumps(results["pe_info"]) if results["pe_info"] else None
        analysis.suspicious_strings = json.dumps(results["suspicious_strings"])
        analysis.suspicious_urls = json.dumps(results["suspicious_urls"] + results.get("suspicious_ips", []))
        analysis.suspicious_apis = json.dumps(results["suspicious_apis"])
        analysis.yara_matches = json.dumps(results["yara_matches"])
        analysis.indicators = json.dumps(results["behavioral_indicators"])
        analysis.analysis_completed_at = datetime.now(timezone.utc)

        await db.flush()
        await db.refresh(analysis)

        logger.info(
            f"Analysis completed for '{file.filename}' | "
            f"Risk: {results['risk_score']}/100 ({results['risk_level']}) | "
            f"YARA matches: {len(results['yara_matches'])}"
        )

    except Exception as e:
        analysis.status = AnalysisStatus.FAILED.value
        analysis.error_message = str(e)
        await db.flush()
        logger.error(f"Analysis failed for '{file.filename}': {e}")

    return FileUploadResponse(
        id=analysis.id,
        filename=analysis.filename,
        original_name=analysis.original_name,
        file_size=analysis.file_size,
        file_type=analysis.file_type,
        md5_hash=analysis.md5_hash,
        sha256_hash=analysis.sha256_hash,
        status=analysis.status,
        message=f"File analyzed successfully. Risk Score: {analysis.risk_score}/100"
        if analysis.status == "completed"
        else f"Analysis failed: {analysis.error_message}",
    )


async def get_analysis_by_id(analysis_id: int, db: AsyncSession) -> FileAnalysisResponse:
    """Get detailed analysis results by ID."""
    result = await db.execute(select(FileAnalysis).where(FileAnalysis.id == analysis_id))
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return _build_analysis_response(analysis)


async def list_analyses(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    risk_level_filter: Optional[str] = None,
) -> FileListResponse:
    """List file analyses with pagination and filtering."""
    offset = (page - 1) * page_size
    query = select(FileAnalysis)

    if status_filter:
        query = query.where(FileAnalysis.status == status_filter)
    if risk_level_filter:
        query = query.where(FileAnalysis.risk_level == risk_level_filter)

    # Count total
    count_query = select(func.count(FileAnalysis.id))
    if status_filter:
        count_query = count_query.where(FileAnalysis.status == status_filter)
    if risk_level_filter:
        count_query = count_query.where(FileAnalysis.risk_level == risk_level_filter)
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Fetch page
    result = await db.execute(
        query.order_by(desc(FileAnalysis.upload_date)).offset(offset).limit(page_size)
    )
    analyses = result.scalars().all()

    return FileListResponse(
        files=[_build_analysis_response(a) for a in analyses],
        total=total,
        page=page,
        page_size=page_size,
    )


def _build_analysis_response(analysis: FileAnalysis) -> FileAnalysisResponse:
    """Build a FileAnalysisResponse from a FileAnalysis model instance."""
    static_analysis = None
    if analysis.status == AnalysisStatus.COMPLETED.value:
        static_analysis = StaticAnalysisResult(
            pe_info=json.loads(analysis.pe_info) if analysis.pe_info else None,
            suspicious_strings=json.loads(analysis.suspicious_strings) if analysis.suspicious_strings else [],
            suspicious_urls=json.loads(analysis.suspicious_urls) if analysis.suspicious_urls else [],
            suspicious_apis=json.loads(analysis.suspicious_apis) if analysis.suspicious_apis else [],
            yara_matches=json.loads(analysis.yara_matches) if analysis.yara_matches else [],
            behavioral_indicators=json.loads(analysis.indicators) if analysis.indicators else [],
        )

    return FileAnalysisResponse(
        id=analysis.id,
        filename=analysis.filename,
        original_name=analysis.original_name,
        file_size=analysis.file_size,
        file_type=analysis.file_type,
        mime_type=analysis.mime_type,
        md5_hash=analysis.md5_hash,
        sha256_hash=analysis.sha256_hash,
        status=analysis.status,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        analysis=static_analysis,
        uploaded_by=analysis.uploaded_by,
        upload_date=analysis.upload_date,
        analysis_completed_at=analysis.analysis_completed_at,
        error_message=analysis.error_message,
    )
