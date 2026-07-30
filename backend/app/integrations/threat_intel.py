"""
ThreatLens AI — Threat Intelligence Feed Integration
Provides IOC (Indicator of Compromise) matching and threat feed correlation.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger("threatlens.integrations.threat_intel")

# ─── Known Threat Intelligence Database (Demo) ────────────────────────
# In production, this would pull from MISP, OTX, Abuse.ch, etc.

KNOWN_MALICIOUS_HASHES = {
    "44d88612fea8a8f36de82e1278abb02f": {"name": "EICAR Test File", "threat_type": "Test", "severity": "Low"},
    "275a021bbfb6489e54d471899f7db9d1": {"name": "EICAR Standard", "threat_type": "Test", "severity": "Low"},
}

KNOWN_MALICIOUS_IPS = {
    "185.220.101.1": {"threat": "TOR Exit Node", "confidence": 0.9},
    "45.33.32.156": {"threat": "Known Scanner", "confidence": 0.7},
    "192.168.1.1": {"threat": "Internal", "confidence": 0.1},
}

KNOWN_MALICIOUS_DOMAINS = {
    "malware.testcategory.com": {"threat": "Malware Distribution", "confidence": 0.95},
    "phishing-example.com": {"threat": "Phishing", "confidence": 0.85},
}

# MITRE ATT&CK technique descriptions
MITRE_TECHNIQUES = {
    "T1055": {"name": "Process Injection", "tactic": "Defense Evasion, Privilege Escalation"},
    "T1056": {"name": "Input Capture", "tactic": "Collection, Credential Access"},
    "T1071": {"name": "Application Layer Protocol", "tactic": "Command and Control"},
    "T1547": {"name": "Boot/Logon Autostart Execution", "tactic": "Persistence, Privilege Escalation"},
    "T1486": {"name": "Data Encrypted for Impact", "tactic": "Impact"},
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution"},
    "T1055.001": {"name": "Dynamic-link Library Injection", "tactic": "Defense Evasion"},
}


class ThreatIntelligenceService:
    """
    Threat intelligence correlation service.

    Checks file indicators (hashes, IPs, URLs) against known
    threat intelligence feeds and returns enrichment data.
    """

    async def check_hash(self, file_hash: str) -> Dict[str, Any]:
        """Check if a file hash is in known threat intelligence."""
        hash_lower = file_hash.lower()
        if hash_lower in KNOWN_MALICIOUS_HASHES:
            info = KNOWN_MALICIOUS_HASHES[hash_lower]
            return {
                "found": True,
                "hash": file_hash,
                "threat_name": info["name"],
                "threat_type": info["threat_type"],
                "severity": info["severity"],
                "source": "ThreatLens Intel DB",
                "last_seen": datetime.now(timezone.utc).isoformat(),
            }
        return {"found": False, "hash": file_hash}

    async def check_iocs(
        self,
        urls: List[str],
        ips: List[str],
    ) -> Dict[str, Any]:
        """
        Check URLs and IPs against threat intelligence feeds.

        Returns enrichment data for any matching IOCs.
        """
        results = {
            "malicious_ips": [],
            "malicious_urls": [],
            "total_iocs_checked": len(urls) + len(ips),
            "matches_found": 0,
        }

        # Check IPs
        for ip in ips:
            if ip in KNOWN_MALICIOUS_IPS:
                info = KNOWN_MALICIOUS_IPS[ip]
                results["malicious_ips"].append({
                    "ip": ip,
                    "threat": info["threat"],
                    "confidence": info["confidence"],
                    "source": "ThreatLens Intel DB",
                })
                results["matches_found"] += 1

        # Check URLs for domain matches
        for url in urls:
            domain = _extract_domain(url)
            if domain and domain in KNOWN_MALICIOUS_DOMAINS:
                info = KNOWN_MALICIOUS_DOMAINS[domain]
                results["malicious_urls"].append({
                    "url": url,
                    "domain": domain,
                    "threat": info["threat"],
                    "confidence": info["confidence"],
                    "source": "ThreatLens Intel DB",
                })
                results["matches_found"] += 1

        return results

    def enrich_mitre_techniques(
        self,
        indicators: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Enrich behavioral indicators with MITRE ATT&CK details.

        Extracts technique IDs from indicator strings and returns
        full technique descriptions.
        """
        enriched = []
        seen = set()

        for indicator in indicators:
            # Extract technique ID (e.g., "T1055" from "Process Injection (T1055)")
            for tech_id, tech_info in MITRE_TECHNIQUES.items():
                if tech_id in indicator and tech_id not in seen:
                    seen.add(tech_id)
                    enriched.append({
                        "technique_id": tech_id,
                        "name": tech_info["name"],
                        "tactic": tech_info["tactic"],
                        "indicator": indicator,
                    })

        return enriched

    async def generate_threat_summary(
        self,
        analysis_result: Dict[str, Any],
        classification: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a comprehensive threat intelligence summary."""
        urls = analysis_result.get("suspicious_urls", [])
        ips = analysis_result.get("suspicious_ips", [])
        indicators = analysis_result.get("behavioral_indicators", [])

        ioc_results = await self.check_iocs(urls, ips)
        mitre_enrichment = self.enrich_mitre_techniques(indicators)

        summary = {
            "risk_assessment": _assess_risk_level(analysis_result, classification),
            "ioc_matches": ioc_results,
            "mitre_techniques": mitre_enrichment,
            "recommended_actions": _generate_recommendations(analysis_result, classification),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return summary


def _extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


def _assess_risk_level(analysis: Dict, classification: Optional[Dict]) -> Dict[str, Any]:
    """Produce a risk assessment summary."""
    risk_score = analysis.get("risk_score", 0)
    level = "Clean"
    if risk_score >= 80: level = "Critical"
    elif risk_score >= 60: level = "High"
    elif risk_score >= 40: level = "Medium"
    elif risk_score >= 20: level = "Low"

    assessment = {
        "overall_risk": level,
        "risk_score": risk_score,
        "factors": [],
    }

    if analysis.get("yara_matches"):
        assessment["factors"].append(f"{len(analysis['yara_matches'])} YARA rule matches")
    if analysis.get("suspicious_apis"):
        assessment["factors"].append(f"{len(analysis['suspicious_apis'])} suspicious API imports")
    if analysis.get("suspicious_urls"):
        assessment["factors"].append(f"{len(analysis['suspicious_urls'])} embedded URLs")
    if classification:
        assessment["factors"].append(f"ML: {classification.get('predicted_class', 'Unknown')} ({classification.get('confidence', 0):.0%})")

    return assessment


def _generate_recommendations(analysis: Dict, classification: Optional[Dict]) -> List[str]:
    """Generate response recommendations based on findings."""
    recommendations = []
    risk = analysis.get("risk_score", 0)

    if risk >= 80:
        recommendations.append("IMMEDIATE: Quarantine the file and isolate affected systems")
        recommendations.append("Conduct full incident response investigation")
        recommendations.append("Check for lateral movement indicators")
    elif risk >= 60:
        recommendations.append("Quarantine the file for further analysis")
        recommendations.append("Review network logs for related C2 communication")
        recommendations.append("Monitor affected endpoint for suspicious activity")
    elif risk >= 40:
        recommendations.append("Flag for analyst review within 24 hours")
        recommendations.append("Block associated IOCs at network perimeter")
    elif risk >= 20:
        recommendations.append("Monitor and log — low priority investigation")
    else:
        recommendations.append("No immediate action required — file appears clean")

    if analysis.get("suspicious_urls"):
        recommendations.append("Block embedded URLs at proxy/firewall")
    if analysis.get("suspicious_ips"):
        recommendations.append("Add suspicious IPs to watchlist")

    return recommendations


_service: Optional[ThreatIntelligenceService] = None

def get_threat_intel_service() -> ThreatIntelligenceService:
    global _service
    if _service is None:
        _service = ThreatIntelligenceService()
    return _service
