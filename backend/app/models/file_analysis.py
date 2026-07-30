"""
ThreatLens AI - File Analysis Model
SQLAlchemy model for tracking uploaded files and their analysis results.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileAnalysis(Base):
    __tablename__ = "file_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    filename = Column(String(255), nullable=False)  # UUID-renamed filename
    original_name = Column(String(500), nullable=False)  # Original upload name
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_type = Column(String(100), nullable=True)  # Detected file type
    mime_type = Column(String(200), nullable=True)  # MIME type
    md5_hash = Column(String(32), nullable=True, index=True)
    sha256_hash = Column(String(64), nullable=True, index=True)
    storage_path = Column(String(500), nullable=False)  # Relative path in uploads/

    # Analysis Results
    status = Column(
        String(20),
        nullable=False,
        default=AnalysisStatus.PENDING.value,
    )
    risk_score = Column(Float, nullable=True)  # 0-100
    risk_level = Column(String(20), nullable=True)  # Critical/High/Medium/Low/Clean

    # Static Analysis Summary (JSON stored as text)
    pe_info = Column(Text, nullable=True)  # PE header info as JSON
    suspicious_strings = Column(Text, nullable=True)  # Suspicious strings as JSON
    suspicious_urls = Column(Text, nullable=True)  # Extracted URLs/IPs as JSON
    suspicious_apis = Column(Text, nullable=True)  # Suspicious API imports as JSON
    yara_matches = Column(Text, nullable=True)  # YARA rule matches as JSON
    indicators = Column(Text, nullable=True)  # Behavioral indicators as JSON

    # Metadata
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    analysis_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<FileAnalysis(id={self.id}, name='{self.original_name}', status='{self.status}')>"
