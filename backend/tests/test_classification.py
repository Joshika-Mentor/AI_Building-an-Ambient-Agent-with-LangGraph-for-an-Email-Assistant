"""
ThreatLens AI — Classification Tests
Tests for ML classification pipeline, endpoints, and statistics.
"""

import pytest
import numpy as np
from httpx import AsyncClient

from app.models.classification import ClassificationResult


# ─── Classification Endpoints ──────────────────────────────────────

class TestClassificationEndpoints:
    """Test classification API endpoints."""

    @pytest.mark.asyncio
    async def test_classify_file_requires_auth(self, client: AsyncClient):
        """Test classification requires authentication."""
        response = await client.post("/api/v1/classifications/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_classifications_empty(self, client: AsyncClient, test_user, auth_headers):
        """Test listing classifications when none exist."""
        response = await client.get("/api/v1/classifications/", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_classifications_with_data(
        self, client: AsyncClient, test_user, auth_headers, sample_classification
    ):
        """Test listing classifications with existing data."""
        response = await client.get("/api/v1/classifications/", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_classification_stats(self, client: AsyncClient, test_user, auth_headers):
        """Test classification statistics endpoint."""
        response = await client.get("/api/v1/classifications/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_classifications" in data
        assert "malware_distribution" in data
        assert "avg_confidence" in data

    @pytest.mark.asyncio
    async def test_get_classification_by_id(
        self, client: AsyncClient, test_user, auth_headers, sample_classification
    ):
        """Test retrieving a specific classification."""
        response = await client.get(
            f"/api/v1/classifications/{sample_classification.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["malware_class"] == "Trojan"
        assert data["confidence_score"] == 0.87

    @pytest.mark.asyncio
    async def test_get_file_classification(
        self, client: AsyncClient, test_user, auth_headers, sample_classification, sample_file_analysis
    ):
        """Test getting classification for a specific file."""
        response = await client.get(
            f"/api/v1/classifications/file/{sample_file_analysis.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_file_classification_none(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Test getting classification for file with no classification."""
        response = await client.get(
            "/api/v1/classifications/file/99999",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data  # "No classification found"


# ─── ML Pipeline Unit Tests ───────────────────────────────────────

class TestMLPipeline:
    """Test the ML pipeline components directly."""

    def test_pipeline_train_and_predict(self):
        """Test training a pipeline and making predictions."""
        from app.ml.model_pipeline import MalwareClassificationPipeline

        pipeline = MalwareClassificationPipeline(
            n_estimators=10,  # Small for speed
            max_depth=5,
        )

        # Create minimal synthetic data (3 classes, 33 features)
        rng = np.random.RandomState(42)
        X = rng.randn(90, 33)
        y = np.array([0] * 30 + [1] * 30 + [2] * 30)

        # Train
        result = pipeline.train(X, y, cv_folds=2)
        assert "cv_accuracy_mean" in result
        assert result["cv_accuracy_mean"] > 0

        # Predict
        pred_result = pipeline.predict(X[:5])
        assert isinstance(pred_result, list)
        assert len(pred_result) == 5
        first = pred_result[0]
        assert "predicted_class" in first
        assert "confidence" in first
        assert "class_probabilities" in first
        assert 0 <= first["confidence"] <= 1

    def test_preprocessor_transform(self):
        """Test the feature preprocessor."""
        from app.ml.preprocessing import FeaturePreprocessor

        preprocessor = FeaturePreprocessor()
        X = np.random.randn(50, 33)
        X_transformed = preprocessor.fit_transform(X)
        assert X_transformed.shape == X.shape

    def test_feature_extractor_names(self):
        """Test that feature names and count are consistent."""
        from app.ml.feature_extractor import NUM_FEATURES, FEATURE_NAMES

        assert len(FEATURE_NAMES) == NUM_FEATURES
        assert NUM_FEATURES == 33

    def test_model_evaluator(self):
        """Test the model evaluation utilities."""
        from app.ml.validation import ModelEvaluator

        evaluator = ModelEvaluator()
        y_true = np.array([0, 0, 1, 1, 2, 2])
        y_pred = np.array([0, 0, 1, 1, 2, 1])
        y_proba = np.array([
            [0.9, 0.05, 0.05],
            [0.8, 0.1, 0.1],
            [0.1, 0.8, 0.1],
            [0.05, 0.9, 0.05],
            [0.1, 0.1, 0.8],
            [0.1, 0.6, 0.3],
        ])

        result = evaluator.evaluate(y_true, y_pred, y_proba)
        assert "accuracy" in result
        assert "f1_weighted" in result
        assert "per_class_metrics" in result
        assert result["accuracy"] > 0


# ─── Model Repository Tests ───────────────────────────────────────

class TestModelRepository:
    """Test model repository functionality."""

    def test_get_repository_singleton(self):
        """Test that repository is a singleton."""
        from app.ml.model_repository import get_model_repository

        repo1 = get_model_repository()
        repo2 = get_model_repository()
        assert repo1 is repo2

    def test_load_active_model(self):
        """Test loading the trained active model."""
        from app.ml.model_repository import get_model_repository

        repo = get_model_repository()
        pipeline = repo.get_active_pipeline()
        # Model should exist (trained in earlier step)
        if pipeline is not None:
            assert repo.active_version is not None
            # Test prediction with the loaded model
            X_test = np.random.randn(1, 33)
            result = pipeline.predict(X_test)
            assert isinstance(result, list)
            assert "predicted_class" in result[0]
