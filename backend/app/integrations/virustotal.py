"""
ThreatLens AI — VirusTotal Integration
External integration with VirusTotal API v3 for hash-based file reputation lookups.
"""

import logging
from typing import Dict, Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("threatlens.integrations.virustotal")

VT_API_BASE = "https://www.virustotal.com/api/v3"


class VirusTotalClient:
    """
    VirusTotal API v3 client.

    Supports:
    - File hash reputation lookup
    - Detection vendor aggregation
    - Graceful fallback when API key is not configured
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.VIRUSTOTAL_API_KEY
        self._enabled = bool(self.api_key)
        if not self._enabled:
            logger.info("VirusTotal integration disabled (no API key configured)")

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    async def lookup_hash(self, file_hash: str) -> Dict[str, Any]:
        """
        Look up a file hash (MD5 or SHA256) on VirusTotal.

        Returns dict with detection results and vendor breakdown.
        """
        if not self._enabled:
            return _mock_vt_response(file_hash)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{VT_API_BASE}/files/{file_hash}",
                    headers={"x-apikey": self.api_key},
                )

                if response.status_code == 404:
                    return {"found": False, "hash": file_hash, "message": "Not found on VirusTotal"}

                if response.status_code == 429:
                    logger.warning("VirusTotal rate limit exceeded")
                    return {"found": False, "hash": file_hash, "message": "Rate limit exceeded"}

                if response.status_code != 200:
                    logger.error(f"VirusTotal API error: {response.status_code}")
                    return {"found": False, "hash": file_hash, "message": f"API error: {response.status_code}"}

                data = response.json().get("data", {})
                attributes = data.get("attributes", {})
                stats = attributes.get("last_analysis_stats", {})
                results = attributes.get("last_analysis_results", {})

                vendor_results = []
                for vendor, detail in results.items():
                    if detail.get("category") in ("malicious", "suspicious"):
                        vendor_results.append({
                            "vendor": vendor,
                            "result": detail.get("result", "Unknown"),
                            "category": detail.get("category"),
                        })

                detections = stats.get("malicious", 0) + stats.get("suspicious", 0)
                total = sum(stats.values())

                return {
                    "found": True,
                    "hash": file_hash,
                    "sha256": attributes.get("sha256", file_hash),
                    "detections": detections,
                    "total_vendors": total,
                    "detection_rate": round(detections / total, 4) if total > 0 else 0,
                    "vendor_results": vendor_results[:20],
                    "tags": attributes.get("tags", []),
                    "reputation": attributes.get("reputation", 0),
                    "type_description": attributes.get("type_description", ""),
                    "meaningful_name": attributes.get("meaningful_name", ""),
                    "stats": stats,
                }

        except httpx.TimeoutException:
            logger.error("VirusTotal API timeout")
            return {"found": False, "hash": file_hash, "message": "Request timed out"}
        except Exception as e:
            logger.error(f"VirusTotal API error: {e}")
            return {"found": False, "hash": file_hash, "message": str(e)}


def _mock_vt_response(file_hash: str) -> Dict[str, Any]:
    """Mock response for demo when API key is not configured."""
    import hashlib
    seed = int(hashlib.md5(file_hash.encode()).hexdigest()[:8], 16)
    detections = seed % 45
    total = 70 + (seed % 5)

    mock_vendors = [
        ("CrowdStrike", "Trojan.Generic"), ("Kaspersky", "HEUR:Trojan.Win32.Generic"),
        ("Microsoft", "Trojan:Win32/Casdet"), ("Symantec", "Trojan.Gen.2"),
        ("BitDefender", "Gen:Variant.Zusy"), ("ESET-NOD32", "Win32/TrojanDropper"),
        ("Malwarebytes", "Malware.AI"), ("McAfee", "GenericRXPP-YS!"),
        ("Avast", "Win32:Trojan-gen"), ("AVG", "Win32:Trojan-gen"),
    ]

    vendor_results = [
        {"vendor": v, "result": r, "category": "malicious"}
        for v, r in mock_vendors[:min(detections, len(mock_vendors))]
    ]

    return {
        "found": True, "hash": file_hash,
        "sha256": file_hash if len(file_hash) == 64 else "mock_sha256",
        "detections": detections, "total_vendors": total,
        "detection_rate": round(detections / total, 4) if total > 0 else 0,
        "vendor_results": vendor_results,
        "tags": ["pe", "trojan"] if detections > 10 else ["pe"],
        "reputation": -detections * 2,
        "type_description": "Win32 EXE",
        "meaningful_name": "suspicious.exe",
        "stats": {"malicious": detections, "suspicious": max(0, detections // 5), "undetected": total - detections, "harmless": 0},
        "_mock": True,
    }


_client: Optional[VirusTotalClient] = None

def get_vt_client() -> VirusTotalClient:
    global _client
    if _client is None:
        _client = VirusTotalClient()
    return _client
