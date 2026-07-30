"""
ThreatLens AI — Feature Extractor
PE Feature Extraction for ML model input.

Extracts a comprehensive numerical feature vector from PE files
for malware classification. This is the bridge between the
Analysis Service and the ML Prediction Service.
"""

import logging
import math
import os
from typing import Dict, Any, List, Optional

import numpy as np

logger = logging.getLogger("threatlens.ml.features")


# ─── Feature Names (ordered) ─────────────────────────────────────────

FEATURE_NAMES = [
    # File-level features
    "file_size",
    "has_mz_header",
    # PE header features
    "number_of_sections",
    "timestamp",
    "entry_point",
    "image_base",
    "is_dll",
    "is_exe",
    # Section features (aggregated)
    "avg_entropy",
    "max_entropy",
    "min_entropy",
    "entropy_std",
    "num_high_entropy_sections",
    "avg_section_raw_size",
    "max_section_raw_size",
    "avg_virtual_to_raw_ratio",
    "num_zero_raw_size_sections",
    "num_anomalous_section_names",
    # Import features
    "suspicious_api_count",
    "has_process_injection_apis",
    "has_keylogger_apis",
    "has_network_apis",
    "has_persistence_apis",
    "has_crypto_apis",
    "has_execution_apis",
    # String features
    "suspicious_string_count",
    "url_count",
    "ip_count",
    # YARA features
    "yara_match_count",
    "yara_critical_count",
    "yara_high_count",
    # Behavioral indicator features
    "behavioral_indicator_count",
    # Static analysis risk score (pre-ML)
    "static_risk_score",
]

NUM_FEATURES = len(FEATURE_NAMES)

# Standard section names for PE executables
STANDARD_SECTIONS = {
    ".text", ".rdata", ".data", ".rsrc", ".reloc",
    ".bss", ".edata", ".idata", ".pdata", ".tls",
    ".debug", ".CRT", ".xdata",
}

# API groups for categorical features
INJECTION_APIS = {"VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "NtUnmapViewOfSection", "QueueUserAPC"}
KEYLOGGER_APIS = {"GetAsyncKeyState", "SetWindowsHookEx"}
NETWORK_APIS = {"URLDownloadToFile", "InternetOpen", "HttpSendRequest"}
PERSISTENCE_APIS = {"RegSetValueEx", "CreateService"}
CRYPTO_APIS = {"CryptEncrypt"}
EXECUTION_APIS = {"WinExec", "ShellExecute"}


def extract_features_from_analysis(analysis_result: Dict[str, Any]) -> np.ndarray:
    """
    Extract a fixed-length feature vector from analysis results.

    Parameters
    ----------
    analysis_result : dict
        The output from `perform_full_analysis()` containing pe_info,
        suspicious_apis, yara_matches, etc.

    Returns
    -------
    np.ndarray
        Feature vector of shape (NUM_FEATURES,)
    """
    features = np.zeros(NUM_FEATURES, dtype=np.float64)
    pe_info = analysis_result.get("pe_info")
    suspicious_apis = analysis_result.get("suspicious_apis", [])
    yara_matches = analysis_result.get("yara_matches", [])
    urls = analysis_result.get("suspicious_urls", [])
    ips = analysis_result.get("suspicious_ips", [])
    suspicious_strings = analysis_result.get("suspicious_strings", [])
    indicators = analysis_result.get("behavioral_indicators", [])
    risk_score = analysis_result.get("risk_score", 0.0)

    # ─── File-level ───────────────────────────────────────────────
    features[0] = analysis_result.get("file_size", 0)
    features[1] = 1.0 if pe_info is not None else 0.0

    # ─── PE header ────────────────────────────────────────────────
    if pe_info:
        features[2] = pe_info.get("number_of_sections", 0)
        # Parse timestamp (could be hex string or int)
        ts = pe_info.get("timestamp", "0")
        try:
            features[3] = float(int(str(ts), 0)) if str(ts) not in ("Simulated", "None") else 0.0
        except (ValueError, TypeError):
            features[3] = 0.0
        # Parse entry point (hex string)
        ep = pe_info.get("entry_point", "0x0")
        try:
            features[4] = float(int(str(ep), 16))
        except (ValueError, TypeError):
            features[4] = 0.0
        # Parse image base
        ib = pe_info.get("image_base", "0x0")
        try:
            features[5] = float(int(str(ib), 16))
        except (ValueError, TypeError):
            features[5] = 0.0
        features[6] = 1.0 if pe_info.get("is_dll") else 0.0
        features[7] = 1.0 if pe_info.get("is_exe") else 0.0

        # ─── Section-level aggregated features ────────────────────
        sections = pe_info.get("sections", [])
        if sections:
            entropies = [s.get("entropy", 0.0) for s in sections]
            raw_sizes = [s.get("raw_size", 0) for s in sections]
            virtual_sizes = [s.get("virtual_size", 0) for s in sections]
            section_names = [s.get("name", "") for s in sections]

            features[8] = float(np.mean(entropies))       # avg_entropy
            features[9] = float(np.max(entropies))         # max_entropy
            features[10] = float(np.min(entropies))        # min_entropy
            features[11] = float(np.std(entropies))        # entropy_std
            features[12] = sum(1 for e in entropies if e > 7.0)  # high entropy sections
            features[13] = float(np.mean(raw_sizes))       # avg raw size
            features[14] = float(np.max(raw_sizes))        # max raw size

            # Virtual-to-raw ratio (indicator of packing)
            vr_ratios = []
            zero_raw = 0
            for vs, rs in zip(virtual_sizes, raw_sizes):
                if rs > 0:
                    vr_ratios.append(vs / rs)
                else:
                    zero_raw += 1
                    vr_ratios.append(0.0)
            features[15] = float(np.mean(vr_ratios)) if vr_ratios else 0.0
            features[16] = zero_raw

            # Anomalous section names (not in standard set)
            anomalous = sum(1 for name in section_names if name.strip() and name not in STANDARD_SECTIONS)
            features[17] = anomalous

    # ─── Import features ──────────────────────────────────────────
    api_funcs = {api.get("function", "") for api in suspicious_apis}
    features[18] = len(suspicious_apis)
    features[19] = 1.0 if INJECTION_APIS & api_funcs else 0.0
    features[20] = 1.0 if KEYLOGGER_APIS & api_funcs else 0.0
    features[21] = 1.0 if NETWORK_APIS & api_funcs else 0.0
    features[22] = 1.0 if PERSISTENCE_APIS & api_funcs else 0.0
    features[23] = 1.0 if CRYPTO_APIS & api_funcs else 0.0
    features[24] = 1.0 if EXECUTION_APIS & api_funcs else 0.0

    # ─── String features ──────────────────────────────────────────
    features[25] = len(suspicious_strings)
    features[26] = len(urls)
    features[27] = len(ips)

    # ─── YARA features ────────────────────────────────────────────
    features[28] = len(yara_matches)
    features[29] = sum(1 for m in yara_matches if m.get("severity") == "critical")
    features[30] = sum(1 for m in yara_matches if m.get("severity") == "high")

    # ─── Behavioral indicators ────────────────────────────────────
    features[31] = len(indicators)

    # ─── Static risk score ────────────────────────────────────────
    features[32] = risk_score

    return features


def get_feature_names() -> List[str]:
    """Return the ordered list of feature names."""
    return FEATURE_NAMES.copy()


def get_feature_importance_map(importances: np.ndarray) -> List[Dict[str, Any]]:
    """
    Map feature importance scores to feature names.

    Parameters
    ----------
    importances : np.ndarray
        Feature importance array from a trained model.

    Returns
    -------
    list of dict
        Sorted list of {name, importance} dicts (descending).
    """
    paired = [
        {"name": name, "importance": round(float(imp), 4)}
        for name, imp in zip(FEATURE_NAMES, importances)
    ]
    return sorted(paired, key=lambda x: x["importance"], reverse=True)
