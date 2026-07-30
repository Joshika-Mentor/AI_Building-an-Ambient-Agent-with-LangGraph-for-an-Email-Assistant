"""
ThreatLens AI — Threat Service
Threat incident management: listing, status updates, notes, and timeline tracking.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import HTTPException

from app.models.threat import ThreatIncident
from app.schemas.threat import ThreatIncidentResponse, ThreatListResponse, ThreatStatusUpdate

logger = logging.getLogger("threatlens.service.threat")


async def list_threats(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    severity: Optional[str] = None,
    status: Optional[str] = None,
) -> ThreatListResponse:
    """List threat incidents with pagination and filtering."""
    offset = (page - 1) * page_size
    query = select(ThreatIncident)
    count_query = select(func.count(ThreatIncident.id))

    if severity:
        query = query.where(ThreatIncident.severity == severity)
        count_query = count_query.where(ThreatIncident.severity == severity)
    if status:
        query = query.where(ThreatIncident.status == status)
        count_query = count_query.where(ThreatIncident.status == status)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    result = await db.execute(
        query.order_by(desc(ThreatIncident.created_at)).offset(offset).limit(page_size)
    )
    threats = result.scalars().all()

    return ThreatListResponse(
        threats=[_build_threat_response(t) for t in threats],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_threat_by_id(
    threat_id: int,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Get detailed threat incident with timeline."""
    result = await db.execute(
        select(ThreatIncident).where(ThreatIncident.id == threat_id)
    )
    threat = result.scalar_one_or_none()

    if not threat:
        raise HTTPException(status_code=404, detail="Threat incident not found")

    response = _build_threat_response(threat)
    response_dict = response.model_dump()

    # Add timeline
    timeline = []
    if threat.timeline:
        try:
            timeline = json.loads(threat.timeline)
        except (json.JSONDecodeError, TypeError):
            timeline = []
    response_dict["timeline"] = timeline
    response_dict["analyst_notes"] = threat.analyst_notes

    return response_dict


async def update_threat_status(
    threat_id: int,
    status_update: ThreatStatusUpdate,
    user_id: int,
    db: AsyncSession,
) -> ThreatIncidentResponse:
    """Update threat status and add to timeline."""
    result = await db.execute(
        select(ThreatIncident).where(ThreatIncident.id == threat_id)
    )
    threat = result.scalar_one_or_none()

    if not threat:
        raise HTTPException(status_code=404, detail="Threat incident not found")

    valid_statuses = ["open", "investigating", "contained", "resolved"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    old_status = threat.status
    threat.status = status_update.status

    if status_update.status == "resolved":
        threat.resolved_at = datetime.now(timezone.utc)

    # Add to timeline
    timeline = []
    if threat.timeline:
        try:
            timeline = json.loads(threat.timeline)
        except (json.JSONDecodeError, TypeError):
            timeline = []

    timeline.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": f"Status changed: {old_status} → {status_update.status}",
        "user_id": user_id,
        "details": status_update.notes or "",
    })
    threat.timeline = json.dumps(timeline)

    if status_update.notes:
        existing_notes = threat.analyst_notes or ""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        threat.analyst_notes = f"{existing_notes}\n[{timestamp}] {status_update.notes}".strip()

    await db.flush()
    await db.refresh(threat)

    logger.info(f"Threat {threat.incident_id} status: {old_status} → {status_update.status}")
    return _build_threat_response(threat)


async def add_threat_notes(
    threat_id: int,
    notes: str,
    user_id: int,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Add analyst notes to a threat incident."""
    result = await db.execute(
        select(ThreatIncident).where(ThreatIncident.id == threat_id)
    )
    threat = result.scalar_one_or_none()

    if not threat:
        raise HTTPException(status_code=404, detail="Threat incident not found")

    # Append notes
    existing = threat.analyst_notes or ""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    threat.analyst_notes = f"{existing}\n[{timestamp}] {notes}".strip()

    # Add to timeline
    timeline = []
    if threat.timeline:
        try:
            timeline = json.loads(threat.timeline)
        except (json.JSONDecodeError, TypeError):
            timeline = []

    timeline.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "Note added",
        "user_id": user_id,
        "details": notes,
    })
    threat.timeline = json.dumps(timeline)

    await db.flush()
    await db.refresh(threat)

    logger.info(f"Notes added to threat {threat.incident_id}")
    return await get_threat_by_id(threat_id, db)


async def get_threat_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get threat incident statistics."""
    total_result = await db.execute(select(func.count(ThreatIncident.id)))
    total = total_result.scalar() or 0

    sev_result = await db.execute(
        select(ThreatIncident.severity, func.count(ThreatIncident.id))
        .group_by(ThreatIncident.severity)
    )
    by_severity = {row[0]: row[1] for row in sev_result.all()}

    stat_result = await db.execute(
        select(ThreatIncident.status, func.count(ThreatIncident.id))
        .group_by(ThreatIncident.status)
    )
    by_status = {row[0]: row[1] for row in stat_result.all()}

    type_result = await db.execute(
        select(ThreatIncident.threat_type, func.count(ThreatIncident.id))
        .where(ThreatIncident.threat_type.isnot(None))
        .group_by(ThreatIncident.threat_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    open_count = by_status.get("open", 0) + by_status.get("investigating", 0)

    return {
        "total_incidents": total,
        "open_incidents": open_count,
        "by_severity": by_severity,
        "by_status": by_status,
        "by_threat_type": by_type,
    }


def _build_threat_response(t: ThreatIncident) -> ThreatIncidentResponse:
    return ThreatIncidentResponse(
        id=t.id,
        incident_id=t.incident_id,
        title=t.title,
        description=t.description,
        severity=t.severity,
        status=t.status,
        threat_type=t.threat_type,
        risk_score=t.risk_score,
        assigned_to=t.assigned_to,
        created_at=t.created_at,
        updated_at=t.updated_at,
        resolved_at=t.resolved_at,
    )
