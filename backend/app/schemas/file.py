"""
ThreatLens AI - File Analysis Schemas
Pydantic models for file upload and analysis responses.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class FileUploadResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int
    file_type: Optional[str] = None
    md5_hash: Optional[str] = None
    sha256_hash: Optional[str] = None
    status: str
    message: str

    model_config = {"from_attributes": True}


class PEHeaderInfo(BaseModel):
    entry_point: Optional[str] = None
    image_base: Optional[str] = None
    number_of_sections: Optional[int] = None
    timestamp: Optional[str] = None
    characteristics: Optional[List[str]] = None
    is_dll: Optional[bool] = None
    is_exe: Optional[bool] = None
    machine_type: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None


class StaticAnalysisResult(BaseModel):
    pe_info: Optional[PEHeaderInfo] = None
    suspicious_strings: Optional[List[str]] = None
    suspicious_urls: Optional[List[str]] = None
    suspicious_ips: Optional[List[str]] = None
    suspicious_apis: Optional[List[Dict[str, str]]] = None
    yara_matches: Optional[List[Dict[str, Any]]] = None
    behavioral_indicators: Optional[List[str]] = None


class FileAnalysisResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    md5_hash: Optional[str] = None
    sha256_hash: Optional[str] = None
    status: str
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    analysis: Optional[StaticAnalysisResult] = None
    uploaded_by: int
    upload_date: datetime
    analysis_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    files: List[FileAnalysisResponse]
    total: int
    page: int
    page_size: int
