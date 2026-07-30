"""
ThreatLens AI — Model Training Script
Standalone script to train the malware classification model.

Generates a synthetic PE-feature dataset for demonstration purposes
and trains the full pipeline: Feature Extraction → Preprocessing → Training → Validation → Save.

Usage:
    cd backend
    python -m app.ml.train
"""

import logging
import os
import sys
import time

import numpy as np

# Add backend to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ml.model_pipeline import (
    MalwareClassificationPipeline,
    MALWARE_CLASSES,
    CLASS_TO_INDEX,
)
from app.ml.model_repository import get_model_repository
from app.ml.validation import ModelEvaluator
from app.ml.feature_extractor import NUM_FEATURES, FEATURE_NAMES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("threatlens.ml.train")


# ─── Synthetic Dataset Generator ─────────────────────────────────────

def generate_synthetic_dataset(
    n_samples_per_class: int = 200,
    random_state: int = 42,
) -> tuple:
    """
    Generate a synthetic dataset mimicking PE malware features.

    Each class has distinct feature distributions to make the model
    learn meaningful patterns. This simulates what real malware analysis
    would produce.

    Parameters
    ----------
    n_samples_per_class : int
        Number of samples per malware class
    random_state : int
        Random seed for reproducibility

    Returns
    -------
    X : np.ndarray of shape (n_total, NUM_FEATURES)
    y : np.ndarray of shape (n_total,) with integer class labels
    """
    rng = np.random.RandomState(random_state)
    all_X = []
    all_y = []

    for cls_name in MALWARE_CLASSES:
        cls_idx = CLASS_TO_INDEX[cls_name]
        X_class = np.zeros((n_samples_per_class, NUM_FEATURES))

        # ─── Feature distributions by malware class ───────────────

        if cls_name == "Clean":
            # Clean files: normal PE structure, low risk signals
            X_class[:, 0] = rng.lognormal(12, 1.5, n_samples_per_class)  # file_size
            X_class[:, 1] = 1.0  # has_mz_header
            X_class[:, 2] = rng.choice([3, 4, 5, 6], n_samples_per_class)  # sections
            X_class[:, 3] = rng.uniform(1.5e9, 1.7e9, n_samples_per_class)  # timestamp
            X_class[:, 4] = rng.uniform(0x1000, 0x5000, n_samples_per_class)  # entry_point
            X_class[:, 5] = 0x400000  # image_base
            X_class[:, 6] = rng.choice([0, 1], n_samples_per_class, p=[0.8, 0.2])  # is_dll
            X_class[:, 7] = 1 - X_class[:, 6]  # is_exe
            X_class[:, 8] = rng.uniform(4.0, 6.0, n_samples_per_class)  # avg_entropy
            X_class[:, 9] = rng.uniform(5.5, 6.8, n_samples_per_class)  # max_entropy
            X_class[:, 10] = rng.uniform(1.0, 3.5, n_samples_per_class)  # min_entropy
            X_class[:, 11] = rng.uniform(0.5, 1.5, n_samples_per_class)  # entropy_std
            X_class[:, 12] = 0  # high entropy sections
            X_class[:, 13] = rng.lognormal(10, 1, n_samples_per_class)  # avg_raw_size
            X_class[:, 14] = rng.lognormal(11, 1, n_samples_per_class)  # max_raw_size
            X_class[:, 15] = rng.uniform(0.8, 1.2, n_samples_per_class)  # vr_ratio
            X_class[:, 16] = 0  # zero raw size
            X_class[:, 17] = rng.choice([0, 1], n_samples_per_class, p=[0.9, 0.1])  # anomalous names
            X_class[:, 18] = rng.choice([0, 1, 2], n_samples_per_class, p=[0.6, 0.3, 0.1])  # sus apis
            X_class[:, 19:25] = 0  # no injection/keylogger/network/persistence/crypto/execution
            X_class[:, 25] = rng.choice([0, 1, 2], n_samples_per_class, p=[0.7, 0.2, 0.1])  # sus strings
            X_class[:, 26] = 0  # url_count
            X_class[:, 27] = 0  # ip_count
            X_class[:, 28] = 0  # yara_match_count
            X_class[:, 29] = 0  # yara_critical
            X_class[:, 30] = 0  # yara_high
            X_class[:, 31] = rng.choice([0, 1], n_samples_per_class, p=[0.8, 0.2])  # behavioral
            X_class[:, 32] = rng.uniform(0, 15, n_samples_per_class)  # risk_score

        elif cls_name == "Trojan":
            # Trojans: process injection, network comms, moderate entropy
            X_class[:, 0] = rng.lognormal(12, 2, n_samples_per_class)
            X_class[:, 1] = 1.0
            X_class[:, 2] = rng.choice([4, 5, 6, 7, 8], n_samples_per_class)
            X_class[:, 3] = rng.uniform(1.4e9, 1.7e9, n_samples_per_class)
            X_class[:, 4] = rng.uniform(0x1000, 0x20000, n_samples_per_class)
            X_class[:, 5] = rng.choice([0x400000, 0x10000000], n_samples_per_class)
            X_class[:, 6] = rng.choice([0, 1], n_samples_per_class, p=[0.6, 0.4])
            X_class[:, 7] = 1 - X_class[:, 6]
            X_class[:, 8] = rng.uniform(5.5, 7.2, n_samples_per_class)
            X_class[:, 9] = rng.uniform(6.5, 7.8, n_samples_per_class)
            X_class[:, 10] = rng.uniform(2.0, 4.5, n_samples_per_class)
            X_class[:, 11] = rng.uniform(1.0, 2.5, n_samples_per_class)
            X_class[:, 12] = rng.choice([0, 1, 2], n_samples_per_class, p=[0.3, 0.5, 0.2])
            X_class[:, 13] = rng.lognormal(10, 1.5, n_samples_per_class)
            X_class[:, 14] = rng.lognormal(12, 1, n_samples_per_class)
            X_class[:, 15] = rng.uniform(1.0, 3.0, n_samples_per_class)
            X_class[:, 16] = rng.choice([0, 1], n_samples_per_class, p=[0.7, 0.3])
            X_class[:, 17] = rng.choice([0, 1, 2], n_samples_per_class, p=[0.4, 0.4, 0.2])
            X_class[:, 18] = rng.randint(3, 10, n_samples_per_class)
            X_class[:, 19] = rng.choice([0, 1], n_samples_per_class, p=[0.2, 0.8])  # injection
            X_class[:, 20] = rng.choice([0, 1], n_samples_per_class, p=[0.6, 0.4])  # keylogger
            X_class[:, 21] = rng.choice([0, 1], n_samples_per_class, p=[0.2, 0.8])  # network
            X_class[:, 22] = rng.choice([0, 1], n_samples_per_class, p=[0.3, 0.7])  # persistence
            X_class[:, 23] = rng.choice([0, 1], n_samples_per_class, p=[0.7, 0.3])  # crypto
            X_class[:, 24] = rng.choice([0, 1], n_samples_per_class, p=[0.3, 0.7])  # execution
            X_class[:, 25] = rng.randint(5, 25, n_samples_per_class)
            X_class[:, 26] = rng.randint(1, 8, n_samples_per_class)
            X_class[:, 27] = rng.randint(0, 5, n_samples_per_class)
            X_class[:, 28] = rng.randint(1, 5, n_samples_per_class)
            X_class[:, 29] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 30] = rng.choice([0, 1, 2], n_samples_per_class, p=[0.3, 0.5, 0.2])
            X_class[:, 31] = rng.randint(3, 7, n_samples_per_class)
            X_class[:, 32] = rng.uniform(55, 90, n_samples_per_class)

        elif cls_name == "Ransomware":
            # Ransomware: crypto APIs, file enumeration, high entropy, high risk
            X_class[:, 0] = rng.lognormal(11, 1.5, n_samples_per_class)
            X_class[:, 1] = 1.0
            X_class[:, 2] = rng.choice([3, 4, 5], n_samples_per_class)
            X_class[:, 3] = rng.uniform(1.6e9, 1.7e9, n_samples_per_class)
            X_class[:, 4] = rng.uniform(0x1000, 0x10000, n_samples_per_class)
            X_class[:, 5] = 0x400000
            X_class[:, 6] = 0
            X_class[:, 7] = 1
            X_class[:, 8] = rng.uniform(6.5, 7.8, n_samples_per_class)
            X_class[:, 9] = rng.uniform(7.2, 7.99, n_samples_per_class)
            X_class[:, 10] = rng.uniform(3.0, 5.5, n_samples_per_class)
            X_class[:, 11] = rng.uniform(1.5, 3.0, n_samples_per_class)
            X_class[:, 12] = rng.choice([1, 2, 3], n_samples_per_class, p=[0.3, 0.5, 0.2])
            X_class[:, 13] = rng.lognormal(10, 1, n_samples_per_class)
            X_class[:, 14] = rng.lognormal(11, 1, n_samples_per_class)
            X_class[:, 15] = rng.uniform(1.0, 2.5, n_samples_per_class)
            X_class[:, 16] = rng.choice([0, 1], n_samples_per_class, p=[0.6, 0.4])
            X_class[:, 17] = rng.choice([0, 1, 2], n_samples_per_class, p=[0.3, 0.4, 0.3])
            X_class[:, 18] = rng.randint(4, 12, n_samples_per_class)
            X_class[:, 19] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 20] = 0
            X_class[:, 21] = rng.choice([0, 1], n_samples_per_class, p=[0.4, 0.6])
            X_class[:, 22] = rng.choice([0, 1], n_samples_per_class, p=[0.3, 0.7])
            X_class[:, 23] = 1  # Always has crypto APIs
            X_class[:, 24] = rng.choice([0, 1], n_samples_per_class, p=[0.4, 0.6])
            X_class[:, 25] = rng.randint(8, 35, n_samples_per_class)
            X_class[:, 26] = rng.randint(0, 5, n_samples_per_class)
            X_class[:, 27] = rng.randint(0, 3, n_samples_per_class)
            X_class[:, 28] = rng.randint(2, 6, n_samples_per_class)
            X_class[:, 29] = rng.choice([0, 1, 2], n_samples_per_class, p=[0.2, 0.5, 0.3])
            X_class[:, 30] = rng.choice([1, 2], n_samples_per_class, p=[0.4, 0.6])
            X_class[:, 31] = rng.randint(4, 8, n_samples_per_class)
            X_class[:, 32] = rng.uniform(70, 100, n_samples_per_class)

        elif cls_name == "Spyware":
            # Spyware: keylogging, network, data exfiltration
            X_class[:, 0] = rng.lognormal(11, 1, n_samples_per_class)
            X_class[:, 1] = 1.0
            X_class[:, 2] = rng.choice([4, 5, 6], n_samples_per_class)
            X_class[:, 3] = rng.uniform(1.5e9, 1.7e9, n_samples_per_class)
            X_class[:, 4] = rng.uniform(0x1000, 0x8000, n_samples_per_class)
            X_class[:, 5] = 0x400000
            X_class[:, 6] = rng.choice([0, 1], n_samples_per_class, p=[0.7, 0.3])
            X_class[:, 7] = 1 - X_class[:, 6]
            X_class[:, 8] = rng.uniform(5.0, 6.8, n_samples_per_class)
            X_class[:, 9] = rng.uniform(6.0, 7.5, n_samples_per_class)
            X_class[:, 10] = rng.uniform(2.5, 4.0, n_samples_per_class)
            X_class[:, 11] = rng.uniform(0.8, 2.0, n_samples_per_class)
            X_class[:, 12] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 13] = rng.lognormal(10, 1, n_samples_per_class)
            X_class[:, 14] = rng.lognormal(11, 1, n_samples_per_class)
            X_class[:, 15] = rng.uniform(0.9, 1.8, n_samples_per_class)
            X_class[:, 16] = 0
            X_class[:, 17] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 18] = rng.randint(4, 9, n_samples_per_class)
            X_class[:, 19] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 20] = 1  # Always has keylogger APIs
            X_class[:, 21] = 1  # Always has network APIs
            X_class[:, 22] = rng.choice([0, 1], n_samples_per_class, p=[0.3, 0.7])
            X_class[:, 23] = rng.choice([0, 1], n_samples_per_class, p=[0.6, 0.4])
            X_class[:, 24] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 25] = rng.randint(6, 20, n_samples_per_class)
            X_class[:, 26] = rng.randint(2, 10, n_samples_per_class)
            X_class[:, 27] = rng.randint(1, 6, n_samples_per_class)
            X_class[:, 28] = rng.randint(1, 4, n_samples_per_class)
            X_class[:, 29] = rng.choice([0, 1], n_samples_per_class, p=[0.6, 0.4])
            X_class[:, 30] = rng.choice([0, 1], n_samples_per_class, p=[0.4, 0.6])
            X_class[:, 31] = rng.randint(3, 6, n_samples_per_class)
            X_class[:, 32] = rng.uniform(50, 85, n_samples_per_class)

        elif cls_name == "Backdoor":
            # Backdoor: network comms, persistence, stealth
            X_class[:, 0] = rng.lognormal(10.5, 1.5, n_samples_per_class)
            X_class[:, 1] = 1.0
            X_class[:, 2] = rng.choice([3, 4, 5, 6], n_samples_per_class)
            X_class[:, 3] = rng.uniform(1.5e9, 1.7e9, n_samples_per_class)
            X_class[:, 4] = rng.uniform(0x1000, 0x15000, n_samples_per_class)
            X_class[:, 5] = rng.choice([0x400000, 0x10000000], n_samples_per_class)
            X_class[:, 6] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 7] = 1 - X_class[:, 6]
            X_class[:, 8] = rng.uniform(5.5, 7.0, n_samples_per_class)
            X_class[:, 9] = rng.uniform(6.5, 7.5, n_samples_per_class)
            X_class[:, 10] = rng.uniform(2.0, 4.0, n_samples_per_class)
            X_class[:, 11] = rng.uniform(1.0, 2.2, n_samples_per_class)
            X_class[:, 12] = rng.choice([0, 1], n_samples_per_class, p=[0.4, 0.6])
            X_class[:, 13] = rng.lognormal(9, 1.5, n_samples_per_class)
            X_class[:, 14] = rng.lognormal(11, 1, n_samples_per_class)
            X_class[:, 15] = rng.uniform(1.0, 2.0, n_samples_per_class)
            X_class[:, 16] = rng.choice([0, 1], n_samples_per_class, p=[0.7, 0.3])
            X_class[:, 17] = rng.choice([0, 1, 2], n_samples_per_class, p=[0.3, 0.5, 0.2])
            X_class[:, 18] = rng.randint(5, 12, n_samples_per_class)
            X_class[:, 19] = rng.choice([0, 1], n_samples_per_class, p=[0.3, 0.7])
            X_class[:, 20] = rng.choice([0, 1], n_samples_per_class, p=[0.7, 0.3])
            X_class[:, 21] = 1  # Always has network APIs
            X_class[:, 22] = 1  # Always has persistence
            X_class[:, 23] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 24] = rng.choice([0, 1], n_samples_per_class, p=[0.3, 0.7])
            X_class[:, 25] = rng.randint(5, 18, n_samples_per_class)
            X_class[:, 26] = rng.randint(2, 8, n_samples_per_class)
            X_class[:, 27] = rng.randint(1, 5, n_samples_per_class)
            X_class[:, 28] = rng.randint(1, 5, n_samples_per_class)
            X_class[:, 29] = rng.choice([0, 1], n_samples_per_class, p=[0.4, 0.6])
            X_class[:, 30] = rng.choice([0, 1, 2], n_samples_per_class, p=[0.3, 0.5, 0.2])
            X_class[:, 31] = rng.randint(3, 7, n_samples_per_class)
            X_class[:, 32] = rng.uniform(55, 90, n_samples_per_class)

        elif cls_name == "Worm":
            # Worm: self-replication, network scanning, resource usage
            X_class[:, 0] = rng.lognormal(11, 1.5, n_samples_per_class)
            X_class[:, 1] = 1.0
            X_class[:, 2] = rng.choice([3, 4, 5], n_samples_per_class)
            X_class[:, 3] = rng.uniform(1.4e9, 1.7e9, n_samples_per_class)
            X_class[:, 4] = rng.uniform(0x1000, 0x10000, n_samples_per_class)
            X_class[:, 5] = 0x400000
            X_class[:, 6] = 0
            X_class[:, 7] = 1
            X_class[:, 8] = rng.uniform(5.0, 6.5, n_samples_per_class)
            X_class[:, 9] = rng.uniform(6.0, 7.3, n_samples_per_class)
            X_class[:, 10] = rng.uniform(2.0, 4.0, n_samples_per_class)
            X_class[:, 11] = rng.uniform(0.8, 1.8, n_samples_per_class)
            X_class[:, 12] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 13] = rng.lognormal(10, 1, n_samples_per_class)
            X_class[:, 14] = rng.lognormal(11, 1, n_samples_per_class)
            X_class[:, 15] = rng.uniform(1.0, 2.0, n_samples_per_class)
            X_class[:, 16] = rng.choice([0, 1], n_samples_per_class, p=[0.6, 0.4])
            X_class[:, 17] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 18] = rng.randint(3, 8, n_samples_per_class)
            X_class[:, 19] = rng.choice([0, 1], n_samples_per_class, p=[0.4, 0.6])
            X_class[:, 20] = 0
            X_class[:, 21] = 1  # Always network
            X_class[:, 22] = rng.choice([0, 1], n_samples_per_class, p=[0.3, 0.7])
            X_class[:, 23] = rng.choice([0, 1], n_samples_per_class, p=[0.7, 0.3])
            X_class[:, 24] = rng.choice([0, 1], n_samples_per_class, p=[0.3, 0.7])
            X_class[:, 25] = rng.randint(3, 15, n_samples_per_class)
            X_class[:, 26] = rng.randint(1, 6, n_samples_per_class)
            X_class[:, 27] = rng.randint(2, 8, n_samples_per_class)  # Many IPs
            X_class[:, 28] = rng.randint(1, 4, n_samples_per_class)
            X_class[:, 29] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 30] = rng.choice([0, 1], n_samples_per_class, p=[0.4, 0.6])
            X_class[:, 31] = rng.randint(2, 6, n_samples_per_class)
            X_class[:, 32] = rng.uniform(45, 80, n_samples_per_class)

        elif cls_name == "Adware":
            # Adware: low risk, some network, minimal suspicious behavior
            X_class[:, 0] = rng.lognormal(12, 1, n_samples_per_class)
            X_class[:, 1] = 1.0
            X_class[:, 2] = rng.choice([4, 5, 6], n_samples_per_class)
            X_class[:, 3] = rng.uniform(1.5e9, 1.7e9, n_samples_per_class)
            X_class[:, 4] = rng.uniform(0x1000, 0x5000, n_samples_per_class)
            X_class[:, 5] = 0x400000
            X_class[:, 6] = rng.choice([0, 1], n_samples_per_class, p=[0.7, 0.3])
            X_class[:, 7] = 1 - X_class[:, 6]
            X_class[:, 8] = rng.uniform(4.5, 6.0, n_samples_per_class)
            X_class[:, 9] = rng.uniform(5.5, 6.5, n_samples_per_class)
            X_class[:, 10] = rng.uniform(2.0, 4.0, n_samples_per_class)
            X_class[:, 11] = rng.uniform(0.5, 1.5, n_samples_per_class)
            X_class[:, 12] = 0
            X_class[:, 13] = rng.lognormal(10, 1, n_samples_per_class)
            X_class[:, 14] = rng.lognormal(11, 1, n_samples_per_class)
            X_class[:, 15] = rng.uniform(0.8, 1.3, n_samples_per_class)
            X_class[:, 16] = 0
            X_class[:, 17] = rng.choice([0, 1], n_samples_per_class, p=[0.7, 0.3])
            X_class[:, 18] = rng.randint(1, 5, n_samples_per_class)
            X_class[:, 19] = 0
            X_class[:, 20] = 0
            X_class[:, 21] = rng.choice([0, 1], n_samples_per_class, p=[0.3, 0.7])
            X_class[:, 22] = rng.choice([0, 1], n_samples_per_class, p=[0.4, 0.6])
            X_class[:, 23] = 0
            X_class[:, 24] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 25] = rng.randint(2, 10, n_samples_per_class)
            X_class[:, 26] = rng.randint(3, 12, n_samples_per_class)  # Many URLs (ads)
            X_class[:, 27] = rng.randint(0, 3, n_samples_per_class)
            X_class[:, 28] = rng.choice([0, 1], n_samples_per_class, p=[0.5, 0.5])
            X_class[:, 29] = 0
            X_class[:, 30] = rng.choice([0, 1], n_samples_per_class, p=[0.6, 0.4])
            X_class[:, 31] = rng.randint(1, 4, n_samples_per_class)
            X_class[:, 32] = rng.uniform(20, 50, n_samples_per_class)

        # Add random noise for realism
        noise = rng.normal(0, 0.05, X_class.shape)
        X_class = np.maximum(0, X_class + noise * np.abs(X_class))

        all_X.append(X_class)
        all_y.append(np.full(n_samples_per_class, cls_idx))

    X = np.vstack(all_X)
    y = np.concatenate(all_y)

    # Shuffle
    indices = rng.permutation(len(y))
    return X[indices], y[indices]


def train_model(
    n_samples_per_class: int = 200,
    description: str = "",
) -> dict:
    """
    Full training pipeline: generate data → train → evaluate → save.

    Returns
    -------
    dict with training results, evaluation metrics, and model version
    """
    logger.info("=" * 60)
    logger.info("ThreatLens AI — ML Model Training")
    logger.info("=" * 60)

    # 1. Generate dataset
    logger.info(f"Generating synthetic dataset ({n_samples_per_class} samples per class)...")
    X, y = generate_synthetic_dataset(n_samples_per_class=n_samples_per_class)
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features, {len(np.unique(y))} classes")

    # 2. Train/test split (80/20)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42,
    )
    logger.info(f"Split: {len(X_train)} train, {len(X_test)} test")

    # 3. Train pipeline
    pipeline = MalwareClassificationPipeline(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
    )
    training_result = pipeline.train(X_train, y_train, cv_folds=5)

    # 4. Evaluate on test set
    evaluator = ModelEvaluator()
    X_test_processed = pipeline.preprocessor.transform(X_test)
    y_pred = pipeline.classifier.predict(X_test_processed)
    y_proba = pipeline.classifier.predict_proba(X_test_processed)

    eval_result = evaluator.evaluate(y_test, y_pred, y_proba)

    # 5. Save model
    repo = get_model_repository()
    save_result = repo.save_model(
        pipeline,
        description=description or "Auto-trained on synthetic PE malware dataset",
        set_active=True,
    )

    # 6. Print results
    logger.info("-" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("-" * 60)
    logger.info(f"  Model Version:      {save_result['version']}")
    logger.info(f"  CV Accuracy:        {training_result['cv_accuracy_mean']:.4f} ± {training_result['cv_accuracy_std']:.4f}")
    logger.info(f"  Test Accuracy:      {eval_result['accuracy']:.4f}")
    logger.info(f"  Test F1 (weighted): {eval_result['f1_weighted']:.4f}")
    logger.info(f"  ROC-AUC:            {eval_result.get('roc_auc_weighted', 'N/A')}")
    logger.info("-" * 60)
    logger.info("Per-class metrics:")
    for pc in eval_result["per_class_metrics"]:
        logger.info(f"  {pc['class']:12s}  P={pc['precision']:.3f}  R={pc['recall']:.3f}  F1={pc['f1_score']:.3f}  (n={pc['support']})")
    logger.info("-" * 60)
    logger.info("Top features:")
    for feat in training_result["top_features"][:10]:
        logger.info(f"  {feat['name']:30s}  {feat['importance']:.4f}")
    logger.info("=" * 60)

    return {
        "training": training_result,
        "evaluation": eval_result,
        "model": save_result,
    }


if __name__ == "__main__":
    result = train_model(
        n_samples_per_class=250,
        description="Initial training on synthetic PE malware dataset (1750 samples)",
    )
    print(f"\n[OK] Model trained and saved as: {result['model']['version']}")
    print(f"[STATS] Test Accuracy: {result['evaluation']['accuracy']:.4f}")
    print(f"[STATS] Test F1: {result['evaluation']['f1_weighted']:.4f}")
