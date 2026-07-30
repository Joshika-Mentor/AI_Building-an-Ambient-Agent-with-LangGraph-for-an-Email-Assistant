"""
ThreatLens AI — Classification Service
CLASSIFICATION SERVICE (Architecture Diagram):
Malware Classification, Confidence Scores, Incident Creation.

Orchestrates the full classification pipeline and manages results.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import HTTPException

from app.models.file_analysis import FileAnalysis, AnalysisStatus
from app.models.classification import ClassificationResult
from app.models.threat import ThreatIncident
from app.models.alert import Alert
from app.schemas.classification import ClassificationResponse, ClassificationStatsResponse
from app.services.ml_prediction_service import predict_malware_class
from app.services.analysis_service import perform_full_analysis
from app.utils.helpers import generate_incident_id, get_risk_level

logger = logging.getLogger("threatlens.service.classification")


async def classify_file(
    file_analysis_id: int,
    user_id: int,
    db: AsyncSession,
) -> ClassificationResponse:
    """
    Run ML classification on a previously analyzed file.

    Pipeline:
    1. Fetch file analysis from DB
    2. Re-extract analysis results (or use cached)
    3. Run ML prediction
    4. Save classification result
    5. Auto-create incident + alert for high-risk detections
    """
    # 1. Get the file analysis
    result = await db.execute(
        select(FileAnalysis).where(FileAnalysis.id == file_analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="File analysis not found")

    if analysis.status != AnalysisStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"File analysis is not completed (status: {analysis.status}). "
                   f"Upload and analyze the file first.",
        )

    # 2. Reconstruct analysis result from stored data
    analysis_result = _reconstruct_analysis_result(analysis)

    # 3. Run ML prediction
    prediction = await predict_malware_class(analysis_result)

    # 4. Save classification result
    classification = ClassificationResult(
        file_analysis_id=file_analysis_id,
        malware_class=prediction["predicted_class"],
        malware_family=prediction.get("malware_family"),
        confidence_score=prediction["confidence"],
        risk_score=prediction["risk_score"],
        model_version=prediction.get("model_version"),
        class_probabilities=json.dumps(prediction.get("class_probabilities", {})),
        classified_by=user_id,
    )

    # 5. Auto-create incident for high-risk
    incident_id = None
    if prediction["risk_score"] >= 60 and prediction["predicted_class"] != "Clean":
        incident_id = await _create_threat_incident(
            prediction, analysis, user_id, db
        )
        classification.incident_id = incident_id

        # Also create alert
        await _create_classification_alert(
            prediction, analysis, incident_id, db
        )

    db.add(classification)
    await db.flush()
    await db.refresh(classification)

    logger.info(
        f"Classification saved: file_id={file_analysis_id} | "
        f"class={prediction['predicted_class']} | "
        f"confidence={prediction['confidence']:.2%} | "
        f"risk={prediction['risk_score']:.1f} | "
        f"incident={incident_id or 'none'}"
    )

    return _build_classification_response(classification)


async def get_classification_by_id(
    classification_id: int,
    db: AsyncSession,
) -> ClassificationResponse:
    """Get a specific classification result."""
    result = await db.execute(
        select(ClassificationResult).where(ClassificationResult.id == classification_id)
    )
    classification = result.scalar_one_or_none()

    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")

    return _build_classification_response(classification)


async def get_classification_by_file(
    file_analysis_id: int,
    db: AsyncSession,
) -> Optional[ClassificationResponse]:
    """Get the latest classification for a file analysis."""
    result = await db.execute(
        select(ClassificationResult)
        .where(ClassificationResult.file_analysis_id == file_analysis_id)
        .order_by(desc(ClassificationResult.classified_at))
    )
    classification = result.scalars().first()

    if not classification:
        return None

    return _build_classification_response(classification)


async def list_classifications(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    malware_class: Optional[str] = None,
) -> Dict[str, Any]:
    """List classifications with pagination and filtering."""
    offset = (page - 1) * page_size
    query = select(ClassificationResult)

    if malware_class:
        query = query.where(ClassificationResult.malware_class == malware_class)

    # Count
    count_query = select(func.count(ClassificationResult.id))
    if malware_class:
        count_query = count_query.where(ClassificationResult.malware_class == malware_class)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Fetch
    result = await db.execute(
        query.order_by(desc(ClassificationResult.classified_at))
        .offset(offset).limit(page_size)
    )
    classifications = result.scalars().all()

    return {
        "classifications": [_build_classification_response(c) for c in classifications],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def get_classification_stats(db: AsyncSession) -> ClassificationStatsResponse:
    """Get classification statistics for analytics."""
    # Total
    total_result = await db.execute(select(func.count(ClassificationResult.id)))
    total = total_result.scalar() or 0

    # Distribution by class
    dist_result = await db.execute(
        select(ClassificationResult.malware_class, func.count(ClassificationResult.id))
        .group_by(ClassificationResult.malware_class)
    )
    distribution = {row[0]: row[1] for row in dist_result.all()}

    # Averages
    avg_result = await db.execute(
        select(
            func.avg(ClassificationResult.confidence_score),
            func.avg(ClassificationResult.risk_score),
        )
    )
    row = avg_result.one()
    avg_confidence = round(float(row[0] or 0), 4)
    avg_risk = round(float(row[1] or 0), 1)

    # Recent 5
    recent_result = await db.execute(
        select(ClassificationResult)
        .order_by(desc(ClassificationResult.classified_at))
        .limit(5)
    )
    recent = recent_result.scalars().all()

    return ClassificationStatsResponse(
        total_classifications=total,
        malware_distribution=distribution,
        avg_confidence=avg_confidence,
        avg_risk_score=avg_risk,
        recent_classifications=[_build_classification_response(c) for c in recent],
    )


# ─── Helpers ─────────────────────────────────────────────────────────

def _reconstruct_analysis_result(analysis: FileAnalysis) -> Dict[str, Any]:
    """Reconstruct the analysis result dict from stored JSON fields."""
    return {
        "file_size": analysis.file_size,
        "pe_info": json.loads(analysis.pe_info) if analysis.pe_info else None,
        "suspicious_strings": json.loads(analysis.suspicious_strings) if analysis.suspicious_strings else [],
        "suspicious_urls": json.loads(analysis.suspicious_urls) if analysis.suspicious_urls else [],
        "suspicious_ips": [],
        "suspicious_apis": json.loads(analysis.suspicious_apis) if analysis.suspicious_apis else [],
        "yara_matches": json.loads(analysis.yara_matches) if analysis.yara_matches else [],
        "behavioral_indicators": json.loads(analysis.indicators) if analysis.indicators else [],
        "risk_score": analysis.risk_score or 0.0,
        "risk_level": analysis.risk_level or "Clean",
    }


def _build_classification_response(c: ClassificationResult) -> ClassificationResponse:
    """Build a classification response from the ORM model."""
    probs = None
    if c.class_probabilities:
        try:
            probs = json.loads(c.class_probabilities)
        except (json.JSONDecodeError, TypeError):
            probs = None

    return ClassificationResponse(
        id=c.id,
        file_analysis_id=c.file_analysis_id,
        malware_class=c.malware_class,
        malware_family=c.malware_family,
        confidence_score=c.confidence_score,
        risk_score=c.risk_score,
        model_version=c.model_version,
        class_probabilities=probs,
        incident_id=c.incident_id,
        classified_at=c.classified_at,
    )


async def _create_threat_incident(
    prediction: Dict[str, Any],
    analysis: FileAnalysis,
    user_id: int,
    db: AsyncSession,
) -> str:
    """Auto-create a threat incident for high-risk classifications."""
    incident_id = generate_incident_id()
    severity = get_risk_level(prediction["risk_score"])

    incident = ThreatIncident(
        incident_id=incident_id,
        title=f"{prediction['predicted_class']} detected: {analysis.original_name}",
        description=(
            f"ML classification identified '{analysis.original_name}' as "
            f"{prediction['predicted_class']}"
            f"{' (family: ' + prediction['malware_family'] + ')' if prediction.get('malware_family') else ''} "
            f"with {prediction['confidence']:.1%} confidence. "
            f"Composite risk score: {prediction['risk_score']}/100."
        ),
        severity=severity,
        status="open",
        threat_type=prediction["predicted_class"],
        related_file_id=analysis.id,
        risk_score=prediction["risk_score"],
        assigned_to=user_id,
        timeline=json.dumps([{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "Incident created",
            "details": f"Auto-generated from ML classification (model: {prediction.get('model_version', 'N/A')})",
        }]),
    )
    db.add(incident)
    await db.flush()

    logger.info(f"Threat incident created: {incident_id} (severity: {severity})")
    return incident_id


async def _create_classification_alert(
    prediction: Dict[str, Any],
    analysis: FileAnalysis,
    incident_id: str,
    db: AsyncSession,
):
    """Auto-create an alert for a classification result."""
    severity = get_risk_level(prediction["risk_score"])

    alert = Alert(
        title=f"Malware Detected: {prediction['predicted_class']} — {analysis.original_name}",
        description=(
            f"File '{analysis.original_name}' classified as {prediction['predicted_class']} "
            f"with {prediction['confidence']:.1%} confidence. "
            f"Risk score: {prediction['risk_score']}/100."
        ),
        severity=severity,
        status="new",
        source="classification",
        alert_type="malware_detected",
        related_file_id=analysis.id,
        metadata_json=json.dumps({
            "malware_class": prediction["predicted_class"],
            "malware_family": prediction.get("malware_family"),
            "confidence": prediction["confidence"],
            "risk_score": prediction["risk_score"],
            "incident_id": incident_id,
            "model_version": prediction.get("model_version"),
        }),
    )
    db.add(alert)
    await db.flush()

    logger.info(f"Alert created for file {analysis.id}: {prediction['predicted_class']}")
