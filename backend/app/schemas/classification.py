"""
ThreatLens AI - Classification Schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class ClassificationResponse(BaseModel):
    id: int
    file_analysis_id: int
    malware_class: str
    malware_family: Optional[str] = None
    confidence_score: float
    risk_score: float
    model_version: Optional[str] = None
    class_probabilities: Optional[Dict[str, float]] = None
    incident_id: Optional[str] = None
    classified_at: datetime

    model_config = {"from_attributes": True}


class ClassificationStatsResponse(BaseModel):
    total_classifications: int
    malware_distribution: Dict[str, int]
    avg_confidence: float
    avg_risk_score: float
    recent_classifications: List[ClassificationResponse]
