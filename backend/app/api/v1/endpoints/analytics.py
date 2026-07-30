"""
ThreatLens AI - Analytics Endpoints
Dashboard statistics and analytics data.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import datetime, timedelta, timezone
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.file_analysis import FileAnalysis
from app.models.alert import Alert
from app.models.classification import ClassificationResult
from app.schemas.analytics import (
    OverviewStats, MalwareDistribution, ThreatTrendsResponse,
    ThreatTrend, RiskDistribution,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewStats)
async def get_overview(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard overview statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Total scans
    total_result = await db.execute(select(func.count(FileAnalysis.id)))
    total_scans = total_result.scalar() or 0

    # Threats detected (risk_score > 50)
    threats_result = await db.execute(
        select(func.count(FileAnalysis.id)).where(FileAnalysis.risk_score > 50)
    )
    threats_detected = threats_result.scalar() or 0

    # Average risk score
    avg_result = await db.execute(
        select(func.avg(FileAnalysis.risk_score)).where(FileAnalysis.risk_score.isnot(None))
    )
    avg_risk = avg_result.scalar() or 0.0

    # Active alerts
    alerts_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.status.in_(["new", "acknowledged", "investigating"]))
    )
    active_alerts = alerts_result.scalar() or 0

    # Scans today
    today_result = await db.execute(
        select(func.count(FileAnalysis.id)).where(FileAnalysis.upload_date >= today_start)
    )
    scans_today = today_result.scalar() or 0

    # Critical alerts
    critical_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.severity == "Critical",
            Alert.status.in_(["new", "acknowledged"])
        )
    )
    critical_alerts = critical_result.scalar() or 0

    return OverviewStats(
        total_scans=total_scans,
        threats_detected=threats_detected,
        average_risk_score=round(float(avg_risk), 1),
        active_alerts=active_alerts,
        scans_today=scans_today,
        critical_alerts=critical_alerts,
    )


@router.get("/malware-distribution", response_model=MalwareDistribution)
async def get_malware_distribution(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get malware type distribution from classifications."""
    result = await db.execute(
        select(
            ClassificationResult.malware_class,
            func.count(ClassificationResult.id)
        ).group_by(ClassificationResult.malware_class)
    )
    rows = result.all()
    distribution = {row[0]: row[1] for row in rows}
    total = sum(distribution.values())

    return MalwareDistribution(distribution=distribution, total=total)


@router.get("/trends", response_model=ThreatTrendsResponse)
async def get_threat_trends(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get threat detection trends over time."""
    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(FileAnalysis.upload_date).label("date"),
            func.count(FileAnalysis.id).label("count"),
            func.avg(FileAnalysis.risk_score).label("risk_avg"),
        )
        .where(FileAnalysis.upload_date >= start_date)
        .group_by(func.date(FileAnalysis.upload_date))
        .order_by(func.date(FileAnalysis.upload_date))
    )
    rows = result.all()

    trends = [
        ThreatTrend(
            date=str(row[0]),
            count=row[1],
            risk_avg=round(float(row[2] or 0), 1),
        )
        for row in rows
    ]

    return ThreatTrendsResponse(trends=trends, period=period)


@router.get("/risk-distribution", response_model=RiskDistribution)
async def get_risk_distribution(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get risk score distribution across all analyses."""
    result = await db.execute(
        select(
            func.count(case((FileAnalysis.risk_score <= 20, 1))).label("clean"),
            func.count(case((FileAnalysis.risk_score.between(21, 40), 1))).label("low"),
            func.count(case((FileAnalysis.risk_score.between(41, 60), 1))).label("medium"),
            func.count(case((FileAnalysis.risk_score.between(61, 80), 1))).label("high"),
            func.count(case((FileAnalysis.risk_score > 80, 1))).label("critical"),
        ).where(FileAnalysis.risk_score.isnot(None))
    )
    row = result.one()

    return RiskDistribution(
        clean=row[0] or 0,
        low=row[1] or 0,
        medium=row[2] or 0,
        high=row[3] or 0,
        critical=row[4] or 0,
    )
