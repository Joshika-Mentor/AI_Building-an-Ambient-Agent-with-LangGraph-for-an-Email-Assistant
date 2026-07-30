"""
ThreatLens AI — ML Prediction Service
ML PREDICTION SERVICE (Architecture Diagram): Threat Prediction, ML Model Processing, Risk Scoring.

Bridges the Analysis Service output and the Classification Service
by running ML inference and computing composite risk scores.
"""

import json
import logging
from typing import Dict, Any, Optional

import numpy as np

from app.ml.feature_extractor import extract_features_from_analysis
from app.ml.preprocessing import validate_features
from app.ml.model_repository import get_model_repository
from app.ml.model_pipeline import INDEX_TO_CLASS

logger = logging.getLogger("threatlens.service.ml_prediction")


async def predict_malware_class(
    analysis_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run ML prediction on analysis results.

    Implements the full ML Prediction Service pipeline:
    1. Extract features from static analysis
    2. Validate feature vector
    3. Run ML model inference
    4. Compute composite risk score
    5. Return prediction with confidence

    Parameters
    ----------
    analysis_result : dict
        Output from perform_full_analysis()

    Returns
    -------
    dict with keys:
        - predicted_class: str (e.g., "Trojan")
        - confidence: float (0-1)
        - risk_score: float (0-100)
        - class_probabilities: dict
        - malware_family: str or None
        - feature_summary: dict
        - model_version: str
    """
    repo = get_model_repository()
    pipeline = repo.get_active_pipeline()

    if pipeline is None:
        logger.warning("No trained ML model available — using heuristic classification")
        return _heuristic_classification(analysis_result)

    # 1. Feature extraction
    features = extract_features_from_analysis(analysis_result)

    # 2. Validate
    is_valid, error = validate_features(features)
    if not is_valid:
        logger.error(f"Feature validation failed: {error}")
        return _heuristic_classification(analysis_result)

    # 3. ML inference
    try:
        prediction = pipeline.predict(features)
    except Exception as e:
        logger.error(f"ML prediction failed: {e}")
        return _heuristic_classification(analysis_result)

    # 4. Composite risk score
    static_risk = analysis_result.get("risk_score", 0.0)
    ml_confidence = prediction["confidence"]
    ml_class = prediction["predicted_class"]

    # Weighted composite risk score
    composite_risk = _compute_composite_risk(
        static_risk=static_risk,
        ml_class=ml_class,
        ml_confidence=ml_confidence,
        yara_matches=analysis_result.get("yara_matches", []),
        indicators=analysis_result.get("behavioral_indicators", []),
    )

    # 5. Feature summary (top contributing features)
    feature_importances = pipeline.get_feature_importances()
    top_features = feature_importances[:5]

    result = {
        "predicted_class": prediction["predicted_class"],
        "confidence": prediction["confidence"],
        "risk_score": composite_risk,
        "class_probabilities": prediction["class_probabilities"],
        "malware_family": prediction["malware_family"],
        "model_version": repo.active_version,
        "feature_summary": {
            "total_features": len(features),
            "top_features": top_features,
        },
    }

    logger.info(
        f"ML Prediction: {result['predicted_class']} "
        f"(confidence: {result['confidence']:.2%}, "
        f"risk: {result['risk_score']:.1f}/100)"
    )

    return result


def _compute_composite_risk(
    static_risk: float,
    ml_class: str,
    ml_confidence: float,
    yara_matches: list,
    indicators: list,
) -> float:
    """
    Compute a composite risk score combining multiple signals.

    Formula:
        score = (ml_class_weight × ml_confidence × 0.40)
              + (static_risk × 0.30)
              + (yara_severity × 0.20)
              + (indicator_count × 0.10)

    Returns score in range [0, 100].
    """
    # ML class base weight
    CLASS_WEIGHTS = {
        "Clean": 0.0,
        "Adware": 35.0,
        "Worm": 65.0,
        "Spyware": 70.0,
        "Trojan": 80.0,
        "Backdoor": 85.0,
        "Ransomware": 95.0,
    }

    ml_weight = CLASS_WEIGHTS.get(ml_class, 50.0)
    ml_score = ml_weight * ml_confidence

    # YARA severity score (out of 100)
    severity_map = {"critical": 25, "high": 15, "medium": 8, "low": 3}
    yara_score = min(100.0, sum(
        severity_map.get(m.get("severity", "low"), 3) for m in yara_matches
    ))

    # Indicator score (out of 100)
    indicator_score = min(100.0, len(indicators) * 12)

    # Weighted composite
    composite = (
        ml_score * 0.40 +
        static_risk * 0.30 +
        yara_score * 0.20 +
        indicator_score * 0.10
    )

    return round(min(100.0, max(0.0, composite)), 1)


def _heuristic_classification(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback heuristic classification when no ML model is available.
    Uses rule-based logic from static analysis results.
    """
    risk_score = analysis_result.get("risk_score", 0.0)
    yara_matches = analysis_result.get("yara_matches", [])
    indicators = analysis_result.get("behavioral_indicators", [])
    indicator_str = " ".join(indicators).lower()

    # Determine class from indicators and YARA
    if risk_score < 15:
        predicted_class = "Clean"
        confidence = 0.85
    elif any("ransomware" in str(m.get("category", "")).lower() for m in yara_matches) or "encryption" in indicator_str:
        predicted_class = "Ransomware"
        confidence = 0.70
    elif any("trojan" in str(m.get("category", "")).lower() for m in yara_matches) or "injection" in indicator_str:
        predicted_class = "Trojan"
        confidence = 0.65
    elif "keylogging" in indicator_str or "input capture" in indicator_str:
        predicted_class = "Spyware"
        confidence = 0.60
    elif "persistence" in indicator_str and "network" in indicator_str:
        predicted_class = "Backdoor"
        confidence = 0.55
    elif risk_score > 50:
        predicted_class = "Trojan"
        confidence = 0.50
    elif risk_score > 25:
        predicted_class = "Adware"
        confidence = 0.55
    else:
        predicted_class = "Clean"
        confidence = 0.75

    # Build probability distribution
    other_classes = [cls for cls in INDEX_TO_CLASS.values() if cls != predicted_class]
    remaining_per_class = round((1.0 - confidence) / len(other_classes), 4)
    class_probs = {cls: remaining_per_class for cls in other_classes}
    class_probs[predicted_class] = confidence

    return {
        "predicted_class": predicted_class,
        "confidence": round(confidence, 4),
        "risk_score": risk_score,
        "class_probabilities": class_probs,
        "malware_family": None,
        "model_version": "heuristic",
        "feature_summary": {
            "total_features": 0,
            "top_features": [],
            "note": "Heuristic classification (no ML model loaded)",
        },
    }
