"""
ThreatLens AI — Preprocessing Pipeline
Feature scaling, encoding, normalization, and data preparation for ML.

This module implements the PREPROCESSING box from the architecture diagram:
Preprocessing → Model Pipeline → Model Repository → Validation
"""

import logging
from typing import Optional, Tuple

import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer

from app.ml.feature_extractor import NUM_FEATURES, FEATURE_NAMES

logger = logging.getLogger("threatlens.ml.preprocessing")


class FeaturePreprocessor:
    """
    Preprocessing pipeline for malware classification features.

    Applies the following transformations in order:
    1. Imputation of missing/NaN values
    2. Log-transform of skewed features (file_size, raw_size, etc.)
    3. Standard scaling (zero mean, unit variance)

    The preprocessor must be fit on training data before use on new samples.
    """

    # Indices of features that should be log-transformed (highly skewed)
    LOG_TRANSFORM_FEATURES = [
        "file_size",
        "entry_point",
        "image_base",
        "avg_section_raw_size",
        "max_section_raw_size",
    ]

    def __init__(self):
        self.imputer = SimpleImputer(strategy="constant", fill_value=0.0)
        self.scaler = StandardScaler()
        self._is_fitted = False
        self._log_indices = [
            FEATURE_NAMES.index(f)
            for f in self.LOG_TRANSFORM_FEATURES
            if f in FEATURE_NAMES
        ]

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def fit(self, X: np.ndarray) -> "FeaturePreprocessor":
        """
        Fit the preprocessor on training data.

        Parameters
        ----------
        X : np.ndarray
            Training feature matrix of shape (n_samples, NUM_FEATURES)

        Returns
        -------
        self
        """
        X_processed = self._apply_log_transform(X.copy())
        X_imputed = self.imputer.fit_transform(X_processed)
        self.scaler.fit(X_imputed)
        self._is_fitted = True
        logger.info(f"Preprocessor fitted on {X.shape[0]} samples, {X.shape[1]} features")
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform features using the fitted preprocessor.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix of shape (n_samples, NUM_FEATURES) or (NUM_FEATURES,)

        Returns
        -------
        np.ndarray
            Transformed feature matrix
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor must be fitted before transform()")

        single = X.ndim == 1
        if single:
            X = X.reshape(1, -1)

        X_processed = self._apply_log_transform(X.copy())
        X_imputed = self.imputer.transform(X_processed)
        X_scaled = self.scaler.transform(X_imputed)

        return X_scaled[0] if single else X_scaled

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(X)
        return self.transform(X)

    def _apply_log_transform(self, X: np.ndarray) -> np.ndarray:
        """Apply log1p transform to skewed features."""
        for idx in self._log_indices:
            if idx < X.shape[-1]:
                if X.ndim == 1:
                    X[idx] = np.log1p(max(0, X[idx]))
                else:
                    X[:, idx] = np.log1p(np.maximum(0, X[:, idx]))
        return X

    def get_params(self) -> dict:
        """Return preprocessor parameters for serialization."""
        return {
            "scaler_mean": self.scaler.mean_.tolist() if self._is_fitted else None,
            "scaler_scale": self.scaler.scale_.tolist() if self._is_fitted else None,
            "num_features": NUM_FEATURES,
            "log_transform_indices": self._log_indices,
        }


def validate_features(features: np.ndarray) -> Tuple[bool, Optional[str]]:
    """
    Validate a feature vector before preprocessing.

    Returns
    -------
    (is_valid, error_message)
    """
    if features is None:
        return False, "Feature vector is None"

    if features.ndim == 1:
        if features.shape[0] != NUM_FEATURES:
            return False, f"Expected {NUM_FEATURES} features, got {features.shape[0]}"
    elif features.ndim == 2:
        if features.shape[1] != NUM_FEATURES:
            return False, f"Expected {NUM_FEATURES} features, got {features.shape[1]}"
    else:
        return False, f"Expected 1D or 2D array, got {features.ndim}D"

    if np.any(np.isnan(features)):
        logger.warning("Feature vector contains NaN values — will be imputed")

    if np.any(np.isinf(features)):
        return False, "Feature vector contains infinite values"

    return True, None
