"""
ThreatLens AI — Alert Service
ALERT SERVICE (Architecture Diagram): Threat Alerts, Notifications, Alert History.

Manages alert lifecycle: creation, acknowledgement, resolution, and querying.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from fastapi import HTTPException

from app.models.alert import Alert
from app.schemas.alert import AlertResponse, AlertListResponse, AlertStatsResponse

logger = logging.getLogger("threatlens.service.alert")


async def list_alerts(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    severity: Optional[str] = None,
    status: Optional[str] = None,
) -> AlertListResponse:
    """List alerts with pagination and filtering."""
    offset = (page - 1) * page_size
    query = select(Alert)
    count_query = select(func.count(Alert.id))

    if severity:
        query = query.where(Alert.severity == severity)
        count_query = count_query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
        count_query = count_query.where(Alert.status == status)

    # Total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Unread count
    unread_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.is_read == False)
    )
    unread_count = unread_result.scalar() or 0

    # Fetch page
    result = await db.execute(
        query.order_by(desc(Alert.created_at)).offset(offset).limit(page_size)
    )
    alerts = result.scalars().all()

    return AlertListResponse(
        alerts=[_build_alert_response(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread_count,
    )


async def get_alert_by_id(alert_id: int, db: AsyncSession) -> AlertResponse:
    """Get a specific alert by ID."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Mark as read
    if not alert.is_read:
        alert.is_read = True
        await db.flush()

    return _build_alert_response(alert)


async def acknowledge_alert(alert_id: int, db: AsyncSession) -> AlertResponse:
    """Acknowledge an alert (change status from new to acknowledged)."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.is_read = True
    await db.flush()
    await db.refresh(alert)

    logger.info(f"Alert {alert_id} acknowledged")
    return _build_alert_response(alert)


async def resolve_alert(alert_id: int, db: AsyncSession) -> AlertResponse:
    """Resolve an alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)
    alert.is_read = True
    await db.flush()
    await db.refresh(alert)

    logger.info(f"Alert {alert_id} resolved")
    return _build_alert_response(alert)


async def assign_alert(
    alert_id: int,
    user_id: int,
    db: AsyncSession,
) -> AlertResponse:
    """Assign an alert to a user."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.assigned_to = user_id
    if alert.status == "new":
        alert.status = "investigating"
    await db.flush()
    await db.refresh(alert)

    logger.info(f"Alert {alert_id} assigned to user {user_id}")
    return _build_alert_response(alert)


async def get_alert_stats(db: AsyncSession) -> AlertStatsResponse:
    """Get alert statistics for dashboard."""
    # Total
    total_result = await db.execute(select(func.count(Alert.id)))
    total = total_result.scalar() or 0

    # By severity
    sev_result = await db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    )
    by_severity = {row[0]: row[1] for row in sev_result.all()}

    # By status
    stat_result = await db.execute(
        select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
    )
    by_status = {row[0]: row[1] for row in stat_result.all()}

    # Recent 5
    recent_result = await db.execute(
        select(Alert).order_by(desc(Alert.created_at)).limit(5)
    )
    recent = recent_result.scalars().all()

    return AlertStatsResponse(
        total_alerts=total,
        by_severity=by_severity,
        by_status=by_status,
        recent_alerts=[_build_alert_response(a) for a in recent],
    )


def _build_alert_response(alert: Alert) -> AlertResponse:
    return AlertResponse(
        id=alert.id,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        status=alert.status,
        source=alert.source,
        alert_type=alert.alert_type,
        related_file_id=alert.related_file_id,
        assigned_to=alert.assigned_to,
        is_read=alert.is_read,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
    )
