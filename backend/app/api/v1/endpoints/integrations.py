"""
ThreatLens AI — Integrations API Endpoints
VirusTotal lookups, threat intelligence, and SIEM event log.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.integrations.virustotal import get_vt_client
from app.integrations.threat_intel import get_threat_intel_service
from app.integrations.siem_connector import get_siem_connector

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("/virustotal/{file_hash}", summary="VirusTotal hash lookup")
async def vt_lookup(
    file_hash: str,
    current_user=Depends(get_current_user),
):
    """
    Look up a file hash (MD5 or SHA256) on VirusTotal.
    Returns detection count, vendor results, and reputation data.
    When no API key is configured, returns realistic mock data for demos.
    """
    client = get_vt_client()
    return await client.lookup_hash(file_hash)


@router.get("/threat-intel/check-hash/{file_hash}", summary="Threat intel hash check")
async def check_hash(
    file_hash: str,
    current_user=Depends(get_current_user),
):
    """Check a hash against threat intelligence feeds."""
    service = get_threat_intel_service()
    return await service.check_hash(file_hash)


@router.post("/threat-intel/enrich", summary="Enrich analysis with threat intel")
async def enrich_analysis(
    file_analysis_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Enrich a file analysis with threat intelligence:
    - IOC matching (IPs, URLs)
    - MITRE ATT&CK technique mapping
    - Risk assessment with recommendations
    """
    import json
    from sqlalchemy import select
    from app.models.file_analysis import FileAnalysis

    result = await db.execute(
        select(FileAnalysis).where(FileAnalysis.id == file_analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File analysis not found")

    # Reconstruct analysis result
    analysis_result = {
        "suspicious_urls": json.loads(analysis.suspicious_urls) if analysis.suspicious_urls else [],
        "suspicious_ips": [],
        "suspicious_apis": json.loads(analysis.suspicious_apis) if analysis.suspicious_apis else [],
        "yara_matches": json.loads(analysis.yara_matches) if analysis.yara_matches else [],
        "behavioral_indicators": json.loads(analysis.indicators) if analysis.indicators else [],
        "risk_score": analysis.risk_score or 0,
    }

    service = get_threat_intel_service()
    return await service.generate_threat_summary(analysis_result)


@router.get("/siem/event-log", summary="SIEM event log")
async def get_siem_event_log(
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_user),
):
    """Get recent SIEM event log entries."""
    connector = get_siem_connector()
    return {
        "events": connector.get_event_log(limit=limit),
        "siem_enabled": connector.is_enabled,
        "webhook_url": connector.webhook_url if connector.is_enabled else None,
    }


@router.get("/status", summary="Integration status")
async def get_integration_status(
    current_user=Depends(get_current_user),
):
    """Check the status of all external integrations."""
    vt = get_vt_client()
    siem = get_siem_connector()

    return {
        "virustotal": {
            "enabled": vt.is_enabled,
            "status": "connected" if vt.is_enabled else "api_key_not_configured",
        },
        "threat_intel": {
            "enabled": True,
            "status": "active",
            "feeds": ["ThreatLens Intel DB", "MITRE ATT&CK"],
        },
        "siem": {
            "enabled": siem.is_enabled,
            "status": "connected" if siem.is_enabled else "webhook_not_configured",
        },
        "notifications": {
            "email_enabled": bool(False),  # Simplified check
            "in_app_enabled": True,
        },
    }
