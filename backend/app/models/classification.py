"""
ThreatLens AI - Classification Result Model
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base


class ClassificationResult(Base):
    __tablename__ = "classification_results"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    file_analysis_id = Column(Integer, ForeignKey("file_analyses.id"), nullable=False, index=True)
    malware_class = Column(String(50), nullable=False)  # Clean, Trojan, Ransomware, etc.
    malware_family = Column(String(100), nullable=True)  # Specific family name
    confidence_score = Column(Float, nullable=False)  # 0.0 - 1.0
    risk_score = Column(Float, nullable=False)  # 0 - 100
    model_version = Column(String(50), nullable=True)
    class_probabilities = Column(Text, nullable=True)  # JSON: per-class probabilities
    incident_id = Column(String(50), nullable=True, index=True)  # Auto-created incident ID
    classified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    classified_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Classification(id={self.id}, class='{self.malware_class}', confidence={self.confidence_score})>"
