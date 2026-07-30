"""
ThreatLens AI — SIEM/SOAR Connector
Webhook-based integration for forwarding security events to SIEM/SOAR platforms.
Supports Splunk, Elastic SIEM, and generic webhook endpoints.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import httpx

from app.core.config import settings

logger = logging.getLogger("threatlens.integrations.siem")


# ─── Event Formats ──────────────────────────────────────────────────

def format_cef(event: Dict[str, Any]) -> str:
    """
    Format event in Common Event Format (CEF) for SIEM ingestion.

    CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
    """
    severity_map = {"Critical": 10, "High": 8, "Medium": 5, "Low": 3, "Clean": 1}
    sev_num = severity_map.get(event.get("severity", "Medium"), 5)

    extensions = []
    if event.get("file_name"):
        extensions.append(f"fname={event['file_name']}")
    if event.get("file_hash"):
        extensions.append(f"fileHash={event['file_hash']}")
    if event.get("risk_score"):
        extensions.append(f"cn1={event['risk_score']} cn1Label=RiskScore")
    if event.get("malware_class"):
        extensions.append(f"cs1={event['malware_class']} cs1Label=MalwareClass")
    if event.get("confidence"):
        extensions.append(f"cn2={int(event['confidence'] * 100)} cn2Label=ConfidencePct")
    if event.get("incident_id"):
        extensions.append(f"externalId={event['incident_id']}")

    ext_str = " ".join(extensions)

    return (
        f"CEF:0|ThreatLens|ThreatLens AI|1.0|"
        f"{event.get('event_type', 'detection')}|"
        f"{event.get('title', 'Security Event')}|"
        f"{sev_num}|{ext_str}"
    )


def format_json_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Format event as a structured JSON payload for SIEM."""
    return {
        "source": "ThreatLens AI",
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event.get("event_type", "malware_detection"),
        "severity": event.get("severity", "Medium"),
        "title": event.get("title", "Security Event"),
        "details": {
            "file_name": event.get("file_name"),
            "file_hash": event.get("file_hash"),
            "malware_class": event.get("malware_class"),
            "malware_family": event.get("malware_family"),
            "confidence": event.get("confidence"),
            "risk_score": event.get("risk_score"),
            "incident_id": event.get("incident_id"),
            "behavioral_indicators": event.get("indicators", []),
            "yara_matches": event.get("yara_matches", []),
        },
        "metadata": {
            "analyst_id": event.get("analyst_id"),
            "model_version": event.get("model_version"),
        },
    }


class SIEMConnector:
    """
    SIEM/SOAR webhook connector.

    Forwards ThreatLens security events to external SIEM platforms
    via webhook endpoints. Supports CEF and JSON formats.
    """

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.SIEM_WEBHOOK_URL
        self._enabled = bool(self.webhook_url)
        self._event_log: List[Dict[str, Any]] = []  # In-memory log for demo
        if self._enabled:
            logger.info(f"SIEM connector enabled: {self.webhook_url}")
        else:
            logger.info("SIEM connector disabled (no webhook URL configured)")

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    async def send_event(
        self,
        event: Dict[str, Any],
        format: str = "json",
    ) -> Dict[str, Any]:
        """
        Send a security event to the SIEM webhook.

        Parameters
        ----------
        event : dict
            Event data with title, severity, file_name, etc.
        format : str
            Output format: 'json' or 'cef'
        """
        # Always log locally
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "format": format,
            "delivered": False,
        }

        if format == "cef":
            payload = format_cef(event)
        else:
            payload = format_json_event(event)

        if not self._enabled:
            log_entry["delivered"] = False
            log_entry["reason"] = "SIEM not configured"
            self._event_log.append(log_entry)
            return {"status": "logged_locally", "format": format, "webhook": None}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if format == "cef":
                    response = await client.post(
                        self.webhook_url,
                        content=payload,
                        headers={"Content-Type": "text/plain"},
                    )
                else:
                    response = await client.post(
                        self.webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                log_entry["delivered"] = response.status_code < 400
                log_entry["status_code"] = response.status_code
                self._event_log.append(log_entry)

                if response.status_code < 400:
                    logger.info(f"SIEM event sent: {event.get('title', 'event')}")
                    return {"status": "delivered", "status_code": response.status_code, "format": format}
                else:
                    logger.warning(f"SIEM webhook returned {response.status_code}")
                    return {"status": "failed", "status_code": response.status_code}

        except Exception as e:
            logger.error(f"SIEM delivery failed: {e}")
            log_entry["error"] = str(e)
            self._event_log.append(log_entry)
            return {"status": "failed", "error": str(e)}

    async def send_malware_detection(
        self,
        file_name: str,
        file_hash: str,
        malware_class: str,
        confidence: float,
        risk_score: float,
        incident_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Convenience method for malware detection events."""
        event = {
            "event_type": "malware_detection",
            "title": f"Malware Detected: {malware_class} — {file_name}",
            "severity": "Critical" if risk_score >= 80 else "High" if risk_score >= 60 else "Medium",
            "file_name": file_name,
            "file_hash": file_hash,
            "malware_class": malware_class,
            "confidence": confidence,
            "risk_score": risk_score,
            "incident_id": incident_id,
            **kwargs,
        }
        return await self.send_event(event)

    def get_event_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent event log entries (for dashboard display)."""
        return list(reversed(self._event_log[-limit:]))


_connector: Optional[SIEMConnector] = None

def get_siem_connector() -> SIEMConnector:
    global _connector
    if _connector is None:
        _connector = SIEMConnector()
    return _connector
