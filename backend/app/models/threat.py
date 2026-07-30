"""
ThreatLens AI - Threat Model
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from app.core.database import Base


class ThreatIncident(Base):
    __tablename__ = "threat_incidents"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    incident_id = Column(String(50), unique=True, nullable=False, index=True)  # TL-XXXX format
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False)  # Critical, High, Medium, Low
    status = Column(String(30), nullable=False, default="open")  # open, investigating, contained, resolved
    threat_type = Column(String(100), nullable=True)
    related_file_id = Column(Integer, ForeignKey("file_analyses.id"), nullable=True)
    related_classification_id = Column(Integer, ForeignKey("classification_results.id"), nullable=True)
    risk_score = Column(Float, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    timeline = Column(Text, nullable=True)  # JSON array of timeline events
    analyst_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<ThreatIncident(id='{self.incident_id}', severity='{self.severity}', status='{self.status}')>"
