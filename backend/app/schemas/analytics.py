"""
ThreatLens AI - Analytics Schemas
"""

from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class OverviewStats(BaseModel):
    total_scans: int
    threats_detected: int
    average_risk_score: float
    active_alerts: int
    scans_today: int
    critical_alerts: int


class MalwareDistribution(BaseModel):
    distribution: Dict[str, int]  # {malware_class: count}
    total: int


class ThreatTrend(BaseModel):
    date: str
    count: int
    risk_avg: float


class ThreatTrendsResponse(BaseModel):
    trends: List[ThreatTrend]
    period: str


class RiskDistribution(BaseModel):
    clean: int      # 0-20
    low: int        # 21-40
    medium: int     # 41-60
    high: int       # 61-80
    critical: int   # 81-100


class PerformanceMetrics(BaseModel):
    avg_analysis_time_seconds: float
    total_scans_today: int
    total_scans_week: int
    total_scans_month: int
    api_response_time_ms: float
