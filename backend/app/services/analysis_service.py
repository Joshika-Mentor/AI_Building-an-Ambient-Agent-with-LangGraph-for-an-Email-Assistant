"""
ThreatLens AI - Analysis Service
ANALYSIS SERVICE (Architecture Diagram): Static Analysis, Feature Extraction, Behavior Parsing.
"""

import json
import logging
import math
from typing import Dict, Any, List, Optional, Tuple

from app.utils.file_utils import extract_strings, extract_urls_and_ips
from app.yara_rules.scanner import get_scanner

logger = logging.getLogger("threatlens.analysis")

# Try to import pefile
try:
    import pefile
    PEFILE_AVAILABLE = True
except ImportError:
    PEFILE_AVAILABLE = False
    logger.warning("pefile not installed. PE analysis will be simulated.")

# Suspicious Windows API calls commonly used by malware
SUSPICIOUS_APIS = {
    "VirtualAlloc": "Memory allocation - potential shellcode injection",
    "VirtualAllocEx": "Remote memory allocation - process injection",
    "VirtualProtect": "Memory protection change - self-modifying code",
    "WriteProcessMemory": "Remote process memory write - code injection",
    "CreateRemoteThread": "Remote thread creation - process injection",
    "NtUnmapViewOfSection": "Process hollowing technique",
    "QueueUserAPC": "APC injection technique",
    "SetWindowsHookEx": "API hooking - potential keylogger",
    "GetAsyncKeyState": "Key state monitoring - keylogger",
    "OpenProcess": "Process access - potential injection target",
    "CreateToolhelp32Snapshot": "Process enumeration",
    "URLDownloadToFile": "File download from URL",
    "WinExec": "Command execution",
    "ShellExecute": "Shell command execution",
    "CreateService": "Service creation - persistence",
    "RegSetValueEx": "Registry modification - persistence",
    "InternetOpen": "Internet connection initialization",
    "HttpSendRequest": "HTTP request - potential C2 communication",
    "CryptEncrypt": "Data encryption - potential ransomware",
    "FindFirstFile": "File enumeration - potential ransomware",
}


def analyze_pe_header(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Perform PE header analysis using pefile.
    Returns detailed PE structure information.
    """
    if not PEFILE_AVAILABLE:
        return _simulate_pe_analysis(file_path)

    try:
        pe = pefile.PE(file_path, fast_load=False)

        # Basic header info
        pe_info = {
            "entry_point": hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
            "image_base": hex(pe.OPTIONAL_HEADER.ImageBase),
            "number_of_sections": pe.FILE_HEADER.NumberOfSections,
            "timestamp": str(pe.FILE_HEADER.TimeDateStamp),
            "is_dll": pe.is_dll(),
            "is_exe": pe.is_exe(),
            "machine_type": hex(pe.FILE_HEADER.Machine),
        }

        # Characteristics
        characteristics = []
        if pe.FILE_HEADER.Characteristics & 0x0002:
            characteristics.append("EXECUTABLE_IMAGE")
        if pe.FILE_HEADER.Characteristics & 0x0020:
            characteristics.append("LARGE_ADDRESS_AWARE")
        if pe.FILE_HEADER.Characteristics & 0x2000:
            characteristics.append("DLL")
        if pe.FILE_HEADER.Characteristics & 0x0100:
            characteristics.append("32BIT_MACHINE")
        pe_info["characteristics"] = characteristics

        # Sections with entropy
        sections = []
        for section in pe.sections:
            try:
                section_name = section.Name.decode('utf-8', errors='ignore').strip('\x00')
            except Exception:
                section_name = "unknown"

            entropy = section.get_entropy()
            sections.append({
                "name": section_name,
                "virtual_size": section.Misc_VirtualSize,
                "raw_size": section.SizeOfRawData,
                "entropy": round(entropy, 2),
                "is_suspicious": entropy > 7.0,  # High entropy = packed/encrypted
            })
        pe_info["sections"] = sections

        pe.close()
        return pe_info

    except Exception as e:
        logger.error(f"PE analysis error: {e}")
        return _simulate_pe_analysis(file_path)


def _simulate_pe_analysis(file_path: str) -> Optional[Dict[str, Any]]:
    """Simulate PE analysis when pefile is not available."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(2)
            if header != b'\x4d\x5a':  # MZ header check
                return None

        return {
            "entry_point": "0x00001000",
            "image_base": "0x00400000",
            "number_of_sections": 4,
            "timestamp": "Simulated",
            "is_dll": file_path.lower().endswith('.dll'),
            "is_exe": file_path.lower().endswith('.exe'),
            "machine_type": "0x14c",
            "characteristics": ["EXECUTABLE_IMAGE", "32BIT_MACHINE"],
            "sections": [
                {"name": ".text", "virtual_size": 45056, "raw_size": 44544, "entropy": 6.45, "is_suspicious": False},
                {"name": ".rdata", "virtual_size": 12288, "raw_size": 11776, "entropy": 5.12, "is_suspicious": False},
                {"name": ".data", "virtual_size": 8192, "raw_size": 7680, "entropy": 3.87, "is_suspicious": False},
                {"name": ".rsrc", "virtual_size": 4096, "raw_size": 3584, "entropy": 4.21, "is_suspicious": False},
            ],
        }
    except Exception:
        return None


def analyze_imports(file_path: str) -> List[Dict[str, str]]:
    """Analyze PE imports and flag suspicious API calls."""
    suspicious_found = []

    if PEFILE_AVAILABLE:
        try:
            pe = pefile.PE(file_path, fast_load=True)
            pe.parse_data_directories(
                directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
            )

            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    dll_name = entry.dll.decode('utf-8', errors='ignore')
                    for imp in entry.imports:
                        if imp.name:
                            func_name = imp.name.decode('utf-8', errors='ignore')
                            if func_name in SUSPICIOUS_APIS:
                                suspicious_found.append({
                                    "dll": dll_name,
                                    "function": func_name,
                                    "description": SUSPICIOUS_APIS[func_name],
                                })
            pe.close()
        except Exception as e:
            logger.error(f"Import analysis error: {e}")
    else:
        # Fallback: scan strings for API names
        strings = extract_strings(file_path, min_length=4)
        for s in strings:
            if s in SUSPICIOUS_APIS:
                suspicious_found.append({
                    "dll": "unknown",
                    "function": s,
                    "description": SUSPICIOUS_APIS[s],
                })

    return suspicious_found


def identify_behavioral_indicators(
    pe_info: Optional[Dict],
    suspicious_apis: List[Dict],
    yara_matches: List[Dict],
    urls: List[str],
    ips: List[str],
) -> List[str]:
    """
    Infer behavioral indicators from static analysis results.
    Maps findings to MITRE ATT&CK-like categories.
    """
    indicators = []

    # API-based indicators
    api_functions = {api["function"] for api in suspicious_apis}

    if {"CreateRemoteThread", "VirtualAllocEx", "WriteProcessMemory"} & api_functions:
        indicators.append("Process Injection (T1055)")
    if {"GetAsyncKeyState", "SetWindowsHookEx"} & api_functions:
        indicators.append("Input Capture / Keylogging (T1056)")
    if {"URLDownloadToFile", "InternetOpen", "HttpSendRequest"} & api_functions:
        indicators.append("Network Communication (T1071)")
    if {"RegSetValueEx", "CreateService"} & api_functions:
        indicators.append("Persistence Mechanism (T1547)")
    if {"CryptEncrypt", "FindFirstFile"} & api_functions:
        indicators.append("Data Encryption (T1486)")
    if {"WinExec", "ShellExecute"} & api_functions:
        indicators.append("Command Execution (T1059)")
    if {"VirtualAlloc", "VirtualProtect"} & api_functions:
        indicators.append("Memory Manipulation (T1055.001)")

    # YARA-based indicators
    for match in yara_matches:
        cat = match.get("category", "")
        if cat == "ransomware":
            indicators.append("Ransomware Behavior Detected")
        elif cat == "trojan":
            indicators.append("Trojan Activity Detected")
        elif cat == "packing":
            indicators.append("Executable Packing Detected")
        elif cat == "obfuscation":
            indicators.append("Code Obfuscation Detected")
        elif cat == "evasion":
            indicators.append("Anti-Analysis Techniques Detected")

    # Network indicators
    if urls:
        indicators.append(f"Embedded URLs Found ({len(urls)})")
    if ips:
        indicators.append(f"Embedded IP Addresses Found ({len(ips)})")

    # PE structure indicators
    if pe_info:
        sections = pe_info.get("sections", [])
        high_entropy = [s for s in sections if s.get("is_suspicious")]
        if high_entropy:
            indicators.append(f"High Entropy Sections ({len(high_entropy)}) - Possible Packing/Encryption")

    return list(set(indicators))  # Deduplicate


def calculate_risk_score(
    pe_info: Optional[Dict],
    suspicious_apis: List[Dict],
    yara_matches: List[Dict],
    urls: List[str],
    ips: List[str],
    suspicious_strings: List[str],
) -> float:
    """
    Calculate a risk score (0-100) based on all analysis indicators.
    Weighted scoring across multiple signal categories.
    """
    score = 0.0

    # YARA matches (up to 35 points)
    severity_weights = {"critical": 15, "high": 10, "medium": 5, "low": 2}
    yara_score = sum(
        severity_weights.get(m.get("severity", "low"), 2) for m in yara_matches
    )
    score += min(35, yara_score)

    # Suspicious API imports (up to 25 points)
    api_score = len(suspicious_apis) * 3
    score += min(25, api_score)

    # Embedded URLs/IPs (up to 10 points)
    network_score = (len(urls) + len(ips)) * 2
    score += min(10, network_score)

    # Suspicious strings (up to 10 points)
    string_score = len(suspicious_strings) * 0.5
    score += min(10, string_score)

    # PE structure anomalies (up to 20 points)
    if pe_info:
        sections = pe_info.get("sections", [])
        high_entropy_count = sum(1 for s in sections if s.get("is_suspicious"))
        score += min(10, high_entropy_count * 5)

        if pe_info.get("number_of_sections", 0) > 8:
            score += 5  # Unusual section count
        if pe_info.get("number_of_sections", 0) == 1:
            score += 5  # Single section (likely packed)

    return min(100.0, round(score, 1))


def filter_suspicious_strings(strings: List[str]) -> List[str]:
    """Filter extracted strings to only those that are security-relevant."""
    suspicious_keywords = [
        "password", "passwd", "login", "admin", "root", "shell",
        "cmd.exe", "powershell", "rundll32", "regsvr32",
        "hack", "exploit", "payload", "inject", "hook",
        "crypto", "encrypt", "decrypt", "ransom",
        "c2", "beacon", "callback", "exfil",
        "mimikatz", "metasploit", "cobalt",
    ]

    suspicious = []
    for s in strings:
        s_lower = s.lower()
        if any(kw in s_lower for kw in suspicious_keywords):
            suspicious.append(s)
        elif s.startswith("http://") or s.startswith("https://"):
            suspicious.append(s)

    return suspicious[:100]  # Cap at 100


async def perform_full_analysis(file_path: str) -> Dict[str, Any]:
    """
    Execute the complete static analysis pipeline on a file.
    Returns comprehensive analysis results.
    """
    results = {
        "pe_info": None,
        "suspicious_strings": [],
        "suspicious_urls": [],
        "suspicious_ips": [],
        "suspicious_apis": [],
        "yara_matches": [],
        "behavioral_indicators": [],
        "risk_score": 0.0,
        "risk_level": "Clean",
    }

    # 1. Extract strings
    all_strings = extract_strings(file_path)
    suspicious_strings = filter_suspicious_strings(all_strings)
    results["suspicious_strings"] = suspicious_strings

    # 2. Extract URLs and IPs
    urls, ips = extract_urls_and_ips(all_strings)
    results["suspicious_urls"] = urls
    results["suspicious_ips"] = ips

    # 3. PE Header Analysis
    pe_info = analyze_pe_header(file_path)
    results["pe_info"] = pe_info

    # 4. Import Analysis
    suspicious_apis = analyze_imports(file_path)
    results["suspicious_apis"] = suspicious_apis

    # 5. YARA Scanning
    scanner = get_scanner()
    yara_matches = scanner.scan_file(file_path)
    results["yara_matches"] = yara_matches

    # 6. Behavioral Indicators
    indicators = identify_behavioral_indicators(
        pe_info, suspicious_apis, yara_matches, urls, ips
    )
    results["behavioral_indicators"] = indicators

    # 7. Risk Score
    risk_score = calculate_risk_score(
        pe_info, suspicious_apis, yara_matches, urls, ips, suspicious_strings
    )
    results["risk_score"] = risk_score

    # 8. Risk Level
    from app.utils.helpers import get_risk_level
    results["risk_level"] = get_risk_level(risk_score)

    return results
