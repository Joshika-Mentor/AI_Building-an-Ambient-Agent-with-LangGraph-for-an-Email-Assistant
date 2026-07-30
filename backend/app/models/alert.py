"""
ThreatLens AI - Alert Model
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False)  # Critical, High, Medium, Low
    status = Column(String(30), nullable=False, default="new")  # new, acknowledged, investigating, resolved
    source = Column(String(100), nullable=True)  # analysis, classification, yara, threat_intel
    alert_type = Column(String(100), nullable=True)  # malware_detected, high_risk, yara_match, etc.
    related_file_id = Column(Integer, ForeignKey("file_analyses.id"), nullable=True)
    related_incident_id = Column(Integer, ForeignKey("threat_incidents.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(Text, nullable=True)  # Additional context as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Alert(id={self.id}, severity='{self.severity}', status='{self.status}')>"
