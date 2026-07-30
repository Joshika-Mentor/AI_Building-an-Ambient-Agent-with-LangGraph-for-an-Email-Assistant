"""
ThreatLens AI — Report Generation Service
Generates comprehensive security reports from analysis data.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.file_analysis import FileAnalysis
from app.models.classification import ClassificationResult
from app.models.threat import ThreatIncident
from app.models.alert import Alert

logger = logging.getLogger("threatlens.service.reports")


async def generate_executive_summary(db: AsyncSession) -> Dict[str, Any]:
    """
    Generate an executive summary report.
    High-level overview of security posture for stakeholders.
    """
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # Total scans
    total_result = await db.execute(select(func.count(FileAnalysis.id)))
    total_scans = total_result.scalar() or 0

    # Scans this week
    week_result = await db.execute(
        select(func.count(FileAnalysis.id)).where(FileAnalysis.upload_date >= seven_days_ago)
    )
    scans_week = week_result.scalar() or 0

    # Scans this month
    month_result = await db.execute(
        select(func.count(FileAnalysis.id)).where(FileAnalysis.upload_date >= thirty_days_ago)
    )
    scans_month = month_result.scalar() or 0

    # Threats detected
    threats_result = await db.execute(
        select(func.count(FileAnalysis.id)).where(FileAnalysis.risk_score > 50)
    )
    threats_count = threats_result.scalar() or 0

    # Average risk
    avg_result = await db.execute(
        select(func.avg(FileAnalysis.risk_score)).where(FileAnalysis.risk_score.isnot(None))
    )
    avg_risk = round(float(avg_result.scalar() or 0), 1)

    # Classification breakdown
    class_result = await db.execute(
        select(ClassificationResult.malware_class, func.count(ClassificationResult.id))
        .group_by(ClassificationResult.malware_class)
    )
    malware_breakdown = {row[0]: row[1] for row in class_result.all()}

    # Open incidents
    open_result = await db.execute(
        select(func.count(ThreatIncident.id)).where(
            ThreatIncident.status.in_(["open", "investigating"])
        )
    )
    open_incidents = open_result.scalar() or 0

    # Unresolved alerts
    alert_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.status.in_(["new", "acknowledged"]))
    )
    unresolved_alerts = alert_result.scalar() or 0

    # Risk distribution
    from sqlalchemy import case
    risk_result = await db.execute(
        select(
            func.count(case((FileAnalysis.risk_score <= 20, 1))).label("clean"),
            func.count(case((FileAnalysis.risk_score.between(21, 40), 1))).label("low"),
            func.count(case((FileAnalysis.risk_score.between(41, 60), 1))).label("medium"),
            func.count(case((FileAnalysis.risk_score.between(61, 80), 1))).label("high"),
            func.count(case((FileAnalysis.risk_score > 80, 1))).label("critical"),
        ).where(FileAnalysis.risk_score.isnot(None))
    )
    risk_row = risk_result.one()
    risk_distribution = {
        "clean": risk_row[0] or 0, "low": risk_row[1] or 0,
        "medium": risk_row[2] or 0, "high": risk_row[3] or 0,
        "critical": risk_row[4] or 0,
    }

    # Threat score (0-100 security health)
    threat_ratio = threats_count / max(total_scans, 1)
    security_score = max(0, round(100 - (threat_ratio * 100) - (open_incidents * 5) - (unresolved_alerts * 2), 1))

    return {
        "report_type": "executive_summary",
        "generated_at": now.isoformat(),
        "period": "Last 30 days",
        "security_score": security_score,
        "overview": {
            "total_scans": total_scans,
            "scans_this_week": scans_week,
            "scans_this_month": scans_month,
            "threats_detected": threats_count,
            "average_risk_score": avg_risk,
            "detection_rate": round(threats_count / max(total_scans, 1) * 100, 1),
        },
        "risk_distribution": risk_distribution,
        "malware_breakdown": malware_breakdown,
        "incident_summary": {
            "open_incidents": open_incidents,
            "unresolved_alerts": unresolved_alerts,
        },
    }


async def generate_file_report(
    file_analysis_id: int,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Generate a detailed report for a specific file analysis."""
    result = await db.execute(
        select(FileAnalysis).where(FileAnalysis.id == file_analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        return {"error": "File analysis not found"}

    # Get classification
    class_result = await db.execute(
        select(ClassificationResult)
        .where(ClassificationResult.file_analysis_id == file_analysis_id)
        .order_by(desc(ClassificationResult.classified_at))
    )
    classification = class_result.scalars().first()

    # Get associated threat incident
    threat = None
    if classification and classification.incident_id:
        threat_result = await db.execute(
            select(ThreatIncident).where(ThreatIncident.incident_id == classification.incident_id)
        )
        threat = threat_result.scalar_one_or_none()

    # Build report
    report: Dict[str, Any] = {
        "report_type": "file_analysis",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_info": {
            "id": analysis.id,
            "original_name": analysis.original_name,
            "file_size": analysis.file_size,
            "file_type": analysis.file_type,
            "mime_type": analysis.mime_type,
            "md5_hash": analysis.md5_hash,
            "sha256_hash": analysis.sha256_hash,
            "upload_date": analysis.upload_date.isoformat() if analysis.upload_date else None,
            "status": analysis.status,
        },
        "risk_assessment": {
            "risk_score": analysis.risk_score,
            "risk_level": analysis.risk_level,
        },
        "static_analysis": {
            "pe_info": json.loads(analysis.pe_info) if analysis.pe_info else None,
            "suspicious_strings": json.loads(analysis.suspicious_strings) if analysis.suspicious_strings else [],
            "suspicious_urls": json.loads(analysis.suspicious_urls) if analysis.suspicious_urls else [],
            "suspicious_apis": json.loads(analysis.suspicious_apis) if analysis.suspicious_apis else [],
            "yara_matches": json.loads(analysis.yara_matches) if analysis.yara_matches else [],
            "behavioral_indicators": json.loads(analysis.indicators) if analysis.indicators else [],
        },
    }

    if classification:
        class_probs = None
        if classification.class_probabilities:
            try:
                class_probs = json.loads(classification.class_probabilities)
            except (json.JSONDecodeError, TypeError):
                class_probs = None

        report["ml_classification"] = {
            "malware_class": classification.malware_class,
            "malware_family": classification.malware_family,
            "confidence_score": classification.confidence_score,
            "risk_score": classification.risk_score,
            "model_version": classification.model_version,
            "class_probabilities": class_probs,
            "classified_at": classification.classified_at.isoformat() if classification.classified_at else None,
            "incident_id": classification.incident_id,
        }

    if threat:
        report["threat_incident"] = {
            "incident_id": threat.incident_id,
            "title": threat.title,
            "severity": threat.severity,
            "status": threat.status,
            "created_at": threat.created_at.isoformat() if threat.created_at else None,
        }

    # Generate recommendations
    risk = analysis.risk_score or 0
    recommendations = []
    if risk >= 80:
        recommendations.extend([
            "CRITICAL: Immediately quarantine this file",
            "Isolate the affected endpoint from the network",
            "Initiate full incident response procedure",
            "Check for lateral movement using associated IOCs",
        ])
    elif risk >= 60:
        recommendations.extend([
            "HIGH: Quarantine the file and prevent execution",
            "Review network logs for C2 communication",
            "Schedule detailed malware analysis",
        ])
    elif risk >= 40:
        recommendations.extend([
            "MEDIUM: Flag for analyst review within 24 hours",
            "Block associated IOCs at perimeter",
        ])
    elif risk >= 20:
        recommendations.append("LOW: Monitor and log — no immediate action needed")
    else:
        recommendations.append("CLEAN: No malicious indicators detected")

    report["recommendations"] = recommendations

    return report


async def generate_threat_landscape_report(db: AsyncSession) -> Dict[str, Any]:
    """Generate a threat landscape report with trends and patterns."""
    now = datetime.now(timezone.utc)

    # Recent classifications with file info
    recent_result = await db.execute(
        select(ClassificationResult, FileAnalysis.original_name)
        .join(FileAnalysis, ClassificationResult.file_analysis_id == FileAnalysis.id)
        .order_by(desc(ClassificationResult.classified_at))
        .limit(20)
    )
    recent = [
        {
            "file_name": row[1],
            "malware_class": row[0].malware_class,
            "malware_family": row[0].malware_family,
            "confidence": row[0].confidence_score,
            "risk_score": row[0].risk_score,
            "date": row[0].classified_at.isoformat() if row[0].classified_at else None,
        }
        for row in recent_result.all()
    ]

    # Top threats by frequency
    top_result = await db.execute(
        select(ClassificationResult.malware_class, func.count(ClassificationResult.id).label("count"))
        .where(ClassificationResult.malware_class != "Clean")
        .group_by(ClassificationResult.malware_class)
        .order_by(desc("count"))
        .limit(10)
    )
    top_threats = [{"class": row[0], "count": row[1]} for row in top_result.all()]

    # Top families
    family_result = await db.execute(
        select(ClassificationResult.malware_family, func.count(ClassificationResult.id).label("count"))
        .where(ClassificationResult.malware_family.isnot(None))
        .group_by(ClassificationResult.malware_family)
        .order_by(desc("count"))
        .limit(10)
    )
    top_families = [{"family": row[0], "count": row[1]} for row in family_result.all()]

    # Severity breakdown of incidents
    sev_result = await db.execute(
        select(ThreatIncident.severity, func.count(ThreatIncident.id))
        .group_by(ThreatIncident.severity)
    )
    severity_breakdown = {row[0]: row[1] for row in sev_result.all()}

    return {
        "report_type": "threat_landscape",
        "generated_at": now.isoformat(),
        "recent_detections": recent,
        "top_threats": top_threats,
        "top_families": top_families,
        "severity_breakdown": severity_breakdown,
    }
