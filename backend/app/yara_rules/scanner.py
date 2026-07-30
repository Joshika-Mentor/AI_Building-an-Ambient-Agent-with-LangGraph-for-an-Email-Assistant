"""
ThreatLens AI - YARA Scanner Engine
Compiles and runs YARA rules against uploaded files.
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("threatlens.yara")

# Try to import yara - it may not be installed on all platforms
try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False
    logger.warning("yara-python not installed. YARA scanning will be simulated.")


class YARAScanner:
    """YARA rule scanner for malware detection."""

    def __init__(self, rules_dir: Optional[str] = None):
        self.rules_dir = rules_dir or os.path.join(
            os.path.dirname(__file__), "rules"
        )
        self.compiled_rules = None
        self._compile_rules()

    def _compile_rules(self):
        """Compile all YARA rule files in the rules directory."""
        if not YARA_AVAILABLE:
            logger.info("YARA not available, using simulation mode")
            return

        try:
            rule_files = {}
            if os.path.exists(self.rules_dir):
                for filename in os.listdir(self.rules_dir):
                    if filename.endswith('.yar') or filename.endswith('.yara'):
                        namespace = filename.rsplit('.', 1)[0]
                        filepath = os.path.join(self.rules_dir, filename)
                        rule_files[namespace] = filepath

            if rule_files:
                self.compiled_rules = yara.compile(filepaths=rule_files)
                logger.info(f"Compiled {len(rule_files)} YARA rule files")
            else:
                logger.warning(f"No YARA rule files found in {self.rules_dir}")

        except Exception as e:
            logger.error(f"Failed to compile YARA rules: {e}")
            self.compiled_rules = None

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Scan a file against compiled YARA rules.
        Returns list of matches with rule details.
        """
        if not YARA_AVAILABLE or self.compiled_rules is None:
            return self._simulate_scan(file_path)

        matches = []
        try:
            yara_matches = self.compiled_rules.match(file_path, timeout=30)
            for match in yara_matches:
                match_info = {
                    "rule_name": match.rule,
                    "namespace": match.namespace,
                    "tags": list(match.tags) if match.tags else [],
                    "description": match.meta.get("description", "No description"),
                    "severity": match.meta.get("severity", "medium"),
                    "category": match.meta.get("category", "unknown"),
                    "strings_matched": len(match.strings) if match.strings else 0,
                }
                matches.append(match_info)

        except Exception as e:
            logger.error(f"YARA scan error for {file_path}: {e}")

        return matches

    def _simulate_scan(self, file_path: str) -> List[Dict[str, Any]]:
        """Simulate YARA scanning when yara-python is not available."""
        matches = []

        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024 * 1024)  # Read first 1MB

            content_str = content.decode('ascii', errors='ignore').lower()

            # Simple string-based detection simulation
            detection_rules = [
                {
                    "patterns": ["powershell", "invoke-expression", "downloadstring"],
                    "rule_name": "Suspicious_PowerShell_Commands",
                    "description": "Detects suspicious PowerShell command patterns",
                    "severity": "high",
                    "category": "execution",
                    "min_matches": 2,
                },
                {
                    "patterns": ["createremotethread", "virtualallocex", "writeprocessmemory"],
                    "rule_name": "Trojan_Process_Injection",
                    "description": "Detects process injection techniques",
                    "severity": "critical",
                    "category": "trojan",
                    "min_matches": 2,
                },
                {
                    "patterns": [".encrypted", ".locked", "ransom", "bitcoin", "decrypt"],
                    "rule_name": "Ransomware_Indicators",
                    "description": "Detects ransomware-related strings",
                    "severity": "critical",
                    "category": "ransomware",
                    "min_matches": 2,
                },
                {
                    "patterns": ["upx0", "upx1", "upx!"],
                    "rule_name": "Packed_UPX",
                    "description": "Detects UPX packed executables",
                    "severity": "medium",
                    "category": "packing",
                    "min_matches": 1,
                },
                {
                    "patterns": ["getasynckeystate", "getkeystate", "setwindowshookex", "keylog"],
                    "rule_name": "Trojan_Keylogger",
                    "description": "Detects potential keylogger functionality",
                    "severity": "critical",
                    "category": "trojan",
                    "min_matches": 2,
                },
            ]

            for rule in detection_rules:
                match_count = sum(1 for p in rule["patterns"] if p in content_str)
                if match_count >= rule["min_matches"]:
                    matches.append({
                        "rule_name": rule["rule_name"],
                        "namespace": "simulated",
                        "tags": [],
                        "description": rule["description"],
                        "severity": rule["severity"],
                        "category": rule["category"],
                        "strings_matched": match_count,
                    })

        except Exception as e:
            logger.error(f"Simulated scan error: {e}")

        return matches


# Global scanner instance
_scanner: Optional[YARAScanner] = None


def get_scanner() -> YARAScanner:
    """Get or create the global YARA scanner instance."""
    global _scanner
    if _scanner is None:
        _scanner = YARAScanner()
    return _scanner
