"""
ThreatLens AI — ML Pipeline Unit Tests
Comprehensive tests for feature extraction, preprocessing, model training,
prediction, validation, and repository storage/loading.
"""

import os
import shutil
import tempfile
import numpy as np
import pytest

from app.ml.feature_extractor import (
    NUM_FEATURES,
    FEATURE_NAMES,
    extract_features_from_analysis,
    get_feature_names,
    get_feature_importance_map,
)
from app.ml.preprocessing import FeaturePreprocessor, validate_features
from app.ml.model_pipeline import (
    MalwareClassificationPipeline,
    MALWARE_CLASSES,
    CLASS_TO_INDEX,
    INDEX_TO_CLASS,
)
from app.ml.model_repository import ModelRepository
from app.ml.validation import ModelEvaluator, compare_models
from app.ml.train import generate_synthetic_dataset


# ─── Feature Extractor Tests ─────────────────────────────────────────

def test_feature_extractor_num_features():
    assert len(FEATURE_NAMES) == NUM_FEATURES
    assert len(get_feature_names()) == NUM_FEATURES


def test_extract_features_from_empty_analysis():
    analysis = {}
    features = extract_features_from_analysis(analysis)
    assert isinstance(features, np.ndarray)
    assert features.shape == (NUM_FEATURES,)
    assert features[0] == 0.0  # file_size
    assert features[1] == 0.0  # has_mz_header


def test_extract_features_from_pe_analysis():
    analysis = {
        "file_size": 204800,
        "pe_info": {
            "number_of_sections": 4,
            "timestamp": "0x60000000",
            "entry_point": "0x1000",
            "image_base": "0x400000",
            "is_dll": False,
            "is_exe": True,
            "sections": [
                {"name": ".text", "entropy": 6.2, "raw_size": 102400, "virtual_size": 102400},
                {"name": ".data", "entropy": 4.1, "raw_size": 51200, "virtual_size": 51200},
                {"name": ".rsrc", "entropy": 7.5, "raw_size": 40960, "virtual_size": 40960},
                {"name": ".UPX0", "entropy": 7.9, "raw_size": 0, "virtual_size": 81920},
            ],
        },
        "suspicious_apis": [
            {"function": "VirtualAllocEx"},
            {"function": "WriteProcessMemory"},
            {"function": "CreateRemoteThread"},
        ],
        "yara_matches": [
            {"rule": "UPX_Packed", "severity": "high"},
            {"rule": "Process_Injection", "severity": "critical"},
        ],
        "suspicious_urls": ["http://malicious-c2.com/gate.php"],
        "suspicious_ips": ["192.168.1.100"],
        "suspicious_strings": ["cmd.exe /c", "powershell -enc"],
        "behavioral_indicators": ["Process Hollowing", "Persistence Registry"],
        "risk_score": 85.5,
    }

    features = extract_features_from_analysis(analysis)
    assert features.shape == (NUM_FEATURES,)
    assert features[0] == 204800.0  # file_size
    assert features[1] == 1.0       # has_mz_header
    assert features[2] == 4.0       # sections
    assert features[6] == 0.0       # is_dll
    assert features[7] == 1.0       # is_exe
    assert features[12] == 2.0      # high entropy sections (>7.0)
    assert features[16] == 1.0      # zero raw size sections (.UPX0)
    assert features[17] == 1.0      # anomalous section name (.UPX0)
    assert features[18] == 3.0      # suspicious_api_count
    assert features[19] == 1.0      # has_process_injection_apis
    assert features[26] == 1.0      # url_count
    assert features[28] == 2.0      # yara_match_count
    assert features[29] == 1.0      # yara_critical_count
    assert features[30] == 1.0      # yara_high_count
    assert features[32] == 85.5     # static_risk_score


# ─── Preprocessing Tests ─────────────────────────────────────────────

def test_validate_features():
    valid, err = validate_features(np.zeros(NUM_FEATURES))
    assert valid is True
    assert err is None

    valid, err = validate_features(np.zeros(NUM_FEATURES - 1))
    assert valid is False
    assert "Expected" in err

    valid, err = validate_features(np.array([np.inf] * NUM_FEATURES))
    assert valid is False
    assert "infinite" in err


def test_preprocessor_fit_transform():
    X, _ = generate_synthetic_dataset(n_samples_per_class=10, random_state=42)
    preprocessor = FeaturePreprocessor()
    assert preprocessor.is_fitted is False

    X_transformed = preprocessor.fit_transform(X)
    assert preprocessor.is_fitted is True
    assert X_transformed.shape == X.shape

    # Single sample transform
    single_transformed = preprocessor.transform(X[0])
    assert single_transformed.shape == (NUM_FEATURES,)

    params = preprocessor.get_params()
    assert params["num_features"] == NUM_FEATURES
    assert params["scaler_mean"] is not None


# ─── Model Pipeline & Prediction Tests ──────────────────────────────

def test_pipeline_train_predict():
    X, y = generate_synthetic_dataset(n_samples_per_class=30, random_state=42)
    pipeline = MalwareClassificationPipeline(n_estimators=20, max_depth=5, random_state=42)

    assert pipeline.is_trained is False
    with pytest.raises(RuntimeError):
        pipeline.predict(X[0])

    training_metadata = pipeline.train(X, y, cv_folds=3)
    assert pipeline.is_trained is True
    assert training_metadata["cv_accuracy_mean"] > 0.8
    assert len(training_metadata["classes"]) == 7

    # Single prediction
    pred = pipeline.predict(X[0])
    assert isinstance(pred, dict)
    assert pred["predicted_class"] in MALWARE_CLASSES
    assert 0.0 <= pred["confidence"] <= 1.0
    assert len(pred["class_probabilities"]) == 7
    assert sum(pred["class_probabilities"].values()) == pytest.approx(1.0, abs=0.02)

    # Batch prediction
    batch_pred = pipeline.predict(X[:5])
    assert isinstance(batch_pred, list)
    assert len(batch_pred) == 5

    # Feature importances
    importances = pipeline.get_feature_importances()
    assert len(importances) == NUM_FEATURES
    assert importances[0]["importance"] >= importances[-1]["importance"]


# ─── Model Repository Tests ──────────────────────────────────────────

def test_model_repository_lifecycle():
    temp_dir = tempfile.mkdtemp()
    try:
        repo = ModelRepository(model_dir=temp_dir)
        assert repo.active_version is None

        # Train pipeline
        X, y = generate_synthetic_dataset(n_samples_per_class=20, random_state=42)
        pipeline = MalwareClassificationPipeline(n_estimators=10, max_depth=5)
        pipeline.train(X, y, cv_folds=2)

        # Save model
        saved_meta = repo.save_model(pipeline, version="v1_test", description="Test model", set_active=True)
        assert saved_meta["version"] == "v1_test"
        assert repo.active_version == "v1_test"
        assert len(repo.list_versions()) == 1

        # Load model
        loaded_pipeline = repo.load_model("v1_test")
        assert loaded_pipeline.is_trained is True

        # Test prediction from loaded pipeline
        pred = loaded_pipeline.predict(X[0])
        assert pred["predicted_class"] in MALWARE_CLASSES

        # Delete active version (tests Bug 5 fix!)
        deleted = repo.delete_version("v1_test")
        assert deleted is True
        assert repo.active_version is None
        assert not os.path.exists(os.path.join(temp_dir, "active_model.json"))
        assert len(repo.list_versions()) == 0

    finally:
        shutil.rmtree(temp_dir)


# ─── Model Validation Tests ──────────────────────────────────────────

def test_model_evaluator():
    y_true = np.array([0, 1, 2, 3, 4, 5, 6])
    y_pred = np.array([0, 1, 2, 3, 4, 5, 6])
    evaluator = ModelEvaluator()

    results = evaluator.evaluate(y_true, y_pred)
    assert results["accuracy"] == 1.0
    assert results["f1_weighted"] == 1.0
    assert len(results["per_class_metrics"]) == 7

    # Model comparison
    comp = compare_models([results, results], ["model1", "model2"])
    assert len(comp["comparison_table"]) == 2
    assert comp["best_model"]["name"] == "model1"
