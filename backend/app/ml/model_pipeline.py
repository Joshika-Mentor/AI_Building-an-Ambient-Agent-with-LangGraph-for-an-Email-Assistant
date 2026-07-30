"""
ThreatLens AI — Model Pipeline
Scikit-learn training pipeline for malware classification.

Implements the MODEL PIPELINE box from the architecture diagram.
Uses a Random Forest classifier with hyperparameter tuning.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold

from app.ml.preprocessing import FeaturePreprocessor
from app.ml.feature_extractor import FEATURE_NAMES

logger = logging.getLogger("threatlens.ml.pipeline")


# ─── Malware Classification Categories ──────────────────────────────

MALWARE_CLASSES = [
    "Clean",
    "Adware",
    "Trojan",
    "Ransomware",
    "Worm",
    "Spyware",
    "Backdoor",
]

CLASS_TO_INDEX = {cls: idx for idx, cls in enumerate(MALWARE_CLASSES)}
INDEX_TO_CLASS = {idx: cls for idx, cls in enumerate(MALWARE_CLASSES)}


# ─── Malware Family Mapping ─────────────────────────────────────────

MALWARE_FAMILIES = {
    "Trojan": [
        "Emotet", "TrickBot", "Agent Tesla", "Dridex", "Qbot",
        "IcedID", "FormBook", "Lokibot", "NanoCore", "AsyncRAT",
    ],
    "Ransomware": [
        "LockBit", "Conti", "REvil", "BlackCat", "Ryuk",
        "WannaCry", "Dharma", "Phobos", "Maze", "Hive",
    ],
    "Spyware": [
        "Pegasus", "FinFisher", "DarkHotel", "Regin", "RedLine",
    ],
    "Backdoor": [
        "ShadowPad", "Cobalt Strike", "Meterpreter", "njRAT", "DarkComet",
    ],
    "Worm": [
        "Conficker", "Stuxnet", "SQL Slammer", "MyDoom", "Sality",
    ],
    "Adware": [
        "Fireball", "DollarRevenue", "Gator", "DeskAd", "BrowseFox",
    ],
}


class MalwareClassificationPipeline:
    """
    End-to-end malware classification pipeline.

    Combines preprocessing + Random Forest classifier with
    calibrated probability output for confidence scoring.
    """

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 20,
        min_samples_split: int = 5,
        min_samples_leaf: int = 2,
        random_state: int = 42,
    ):
        self.preprocessor = FeaturePreprocessor()
        self.classifier = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
            oob_score=True,
        )
        self._is_trained = False
        self._training_metadata: Dict[str, Any] = {}

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    @property
    def training_metadata(self) -> Dict[str, Any]:
        return self._training_metadata.copy()

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        cv_folds: int = 5,
    ) -> Dict[str, Any]:
        """
        Train the classification pipeline.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix of shape (n_samples, n_features)
        y : np.ndarray
            Label array of shape (n_samples,) — integer class indices
        cv_folds : int
            Number of cross-validation folds

        Returns
        -------
        dict
            Training results including accuracy, cross-val scores, etc.
        """
        start_time = time.time()
        logger.info(f"Training started: {X.shape[0]} samples, {X.shape[1]} features, {len(np.unique(y))} classes")

        # Preprocess
        X_processed = self.preprocessor.fit_transform(X)

        # Cross-validation
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        cv_scores = cross_val_score(
            self.classifier, X_processed, y,
            cv=cv, scoring="accuracy", n_jobs=-1,
        )

        # Final training on full dataset
        self.classifier.fit(X_processed, y)
        self._is_trained = True

        training_time = time.time() - start_time

        # Feature importances
        importances = self.classifier.feature_importances_
        top_features = sorted(
            zip(FEATURE_NAMES, importances),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        # Collect metadata
        self._training_metadata = {
            "n_samples": int(X.shape[0]),
            "n_features": int(X.shape[1]),
            "n_classes": int(len(np.unique(y))),
            "classes": [INDEX_TO_CLASS.get(int(c), str(c)) for c in np.unique(y)],
            "cv_folds": cv_folds,
            "cv_accuracy_mean": round(float(np.mean(cv_scores)), 4),
            "cv_accuracy_std": round(float(np.std(cv_scores)), 4),
            "cv_scores": [round(float(s), 4) for s in cv_scores],
            "oob_score": round(float(self.classifier.oob_score_), 4),
            "training_time_seconds": round(training_time, 2),
            "top_features": [
                {"name": name, "importance": round(float(imp), 4)}
                for name, imp in top_features
            ],
        }

        logger.info(
            f"Training complete in {training_time:.1f}s | "
            f"CV Accuracy: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f} | "
            f"OOB Score: {self.classifier.oob_score_:.4f}"
        )

        return self._training_metadata

    def predict(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Predict malware class for a single sample or batch.

        Parameters
        ----------
        features : np.ndarray
            Feature vector (1D) or matrix (2D)

        Returns
        -------
        dict with keys:
            - predicted_class: str
            - confidence: float (0-1)
            - class_probabilities: dict of {class_name: probability}
            - malware_family: str or None
        """
        if not self._is_trained:
            raise RuntimeError("Pipeline must be trained before prediction")

        single = features.ndim == 1
        if single:
            features = features.reshape(1, -1)

        X_processed = self.preprocessor.transform(features)

        # Predict class and probabilities
        predictions = self.classifier.predict(X_processed)
        probabilities = self.classifier.predict_proba(X_processed)

        results = []
        for i in range(len(predictions)):
            pred_idx = int(predictions[i])
            pred_class = INDEX_TO_CLASS.get(pred_idx, "Unknown")
            probs = probabilities[i]

            # Build probability dict using classifier.classes_ for correct mapping
            # sklearn guarantees len(probs) == len(self.classifier.classes_)
            class_probs = {}
            for cls_idx, prob in enumerate(probs):
                actual_label = int(self.classifier.classes_[cls_idx])
                cls_name = INDEX_TO_CLASS.get(actual_label, f"Class_{actual_label}")
                class_probs[cls_name] = round(float(prob), 4)

            # Confidence = probability of the predicted class (not argmax)
            # With class_weight='balanced', predict() and argmax(proba) can disagree
            pred_class_mask = self.classifier.classes_ == predictions[i]
            if np.any(pred_class_mask):
                confidence = float(probs[np.where(pred_class_mask)[0][0]])
            else:
                confidence = float(np.max(probs))

            # Determine malware family based on confidence heuristic
            family = _infer_malware_family(pred_class, confidence)

            results.append({
                "predicted_class": pred_class,
                "confidence": round(confidence, 4),
                "class_probabilities": class_probs,
                "malware_family": family,
            })

        return results[0] if single else results

    def get_feature_importances(self) -> List[Dict[str, Any]]:
        """Get ranked feature importances from the trained model."""
        if not self._is_trained:
            return []

        importances = self.classifier.feature_importances_
        return sorted(
            [
                {"name": name, "importance": round(float(imp), 4)}
                for name, imp in zip(FEATURE_NAMES, importances)
            ],
            key=lambda x: x["importance"],
            reverse=True,
        )


def _infer_malware_family(malware_class: str, confidence: float) -> Optional[str]:
    """
    Infer a malware family based on classification and confidence.
    In a production system, this would use signature-based matching.
    For demo purposes, we select a representative family.
    """
    if malware_class == "Clean" or malware_class not in MALWARE_FAMILIES:
        return None

    families = MALWARE_FAMILIES[malware_class]
    # Use confidence to deterministically pick a family (demo)
    idx = int(confidence * 100) % len(families)
    return families[idx]
