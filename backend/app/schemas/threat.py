"""
ThreatLens AI - Threat Schemas
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ThreatIncidentResponse(BaseModel):
    id: int
    incident_id: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    threat_type: Optional[str] = None
    risk_score: Optional[float] = None
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ThreatListResponse(BaseModel):
    threats: List[ThreatIncidentResponse]
    total: int
    page: int
    page_size: int


class ThreatStatusUpdate(BaseModel):
    status: str  # open, investigating, contained, resolved
    notes: Optional[str] = None
