"""
ThreatLens AI - Alert Schemas
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AlertResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    source: Optional[str] = None
    alert_type: Optional[str] = None
    related_file_id: Optional[int] = None
    assigned_to: Optional[int] = None
    is_read: bool
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int
    unread_count: int


class AlertStatsResponse(BaseModel):
    total_alerts: int
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    recent_alerts: List[AlertResponse]
