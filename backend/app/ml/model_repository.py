"""
ThreatLens AI — Model Repository
Model versioning, storage, loading, and metadata management.

Implements the MODEL REPOSITORY box from the architecture diagram.
Handles serialization with joblib and versioned model storage.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import joblib

from app.ml.model_pipeline import MalwareClassificationPipeline

logger = logging.getLogger("threatlens.ml.repository")


# Default model directory relative to backend root
DEFAULT_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "models"
)


class ModelRepository:
    """
    Manages trained model lifecycle: save, load, version, and hot-swap.

    Directory Structure:
        ml/models/
        ├── model_v1_20260704_120000.joblib
        ├── model_v1_20260704_120000.meta.json
        ├── model_v2_20260705_090000.joblib
        ├── model_v2_20260705_090000.meta.json
        └── active_model.json   ← Points to current active version
    """

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or DEFAULT_MODEL_DIR
        os.makedirs(self.model_dir, exist_ok=True)
        self._active_pipeline: Optional[MalwareClassificationPipeline] = None
        self._active_version: Optional[str] = None
        self._active_metadata: Optional[Dict[str, Any]] = None

    @property
    def active_version(self) -> Optional[str]:
        return self._active_version

    @property
    def active_metadata(self) -> Optional[Dict[str, Any]]:
        return self._active_metadata

    def save_model(
        self,
        pipeline: MalwareClassificationPipeline,
        version: Optional[str] = None,
        description: str = "",
        set_active: bool = True,
    ) -> Dict[str, Any]:
        """
        Save a trained pipeline with metadata.

        Parameters
        ----------
        pipeline : MalwareClassificationPipeline
            The trained pipeline to save
        version : str, optional
            Version string. Auto-generated if not provided.
        description : str
            Human-readable description
        set_active : bool
            Whether to set this as the active model

        Returns
        -------
        dict
            Saved model metadata
        """
        if not pipeline.is_trained:
            raise ValueError("Cannot save an untrained pipeline")

        # Generate version
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if version is None:
            # Count existing versions
            existing = self.list_versions()
            version_num = len(existing) + 1
            version = f"v{version_num}_{timestamp}"

        # File paths
        model_filename = f"model_{version}.joblib"
        meta_filename = f"model_{version}.meta.json"
        model_path = os.path.join(self.model_dir, model_filename)
        meta_path = os.path.join(self.model_dir, meta_filename)

        # Metadata
        metadata = {
            "version": version,
            "description": description,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "model_filename": model_filename,
            "training_metadata": pipeline.training_metadata,
            "feature_importances": pipeline.get_feature_importances()[:15],
        }

        # Save model
        model_data = {
            "preprocessor": pipeline.preprocessor,
            "classifier": pipeline.classifier,
        }
        joblib.dump(model_data, model_path, compress=3)

        # Save metadata
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        file_size = os.path.getsize(model_path)
        metadata["file_size_bytes"] = file_size

        logger.info(
            f"Model saved: {version} | "
            f"Size: {file_size / 1024:.1f}KB | "
            f"Accuracy: {metadata['training_metadata'].get('cv_accuracy_mean', 'N/A')}"
        )

        if set_active:
            self._set_active_version(version, metadata)

        return metadata

    def load_model(self, version: Optional[str] = None) -> MalwareClassificationPipeline:
        """
        Load a model by version (or the active model).

        Parameters
        ----------
        version : str, optional
            Specific version to load. Loads active if not specified.

        Returns
        -------
        MalwareClassificationPipeline
        """
        if version is None:
            version = self._get_active_version()
            if version is None:
                # Try to find the latest model
                versions = self.list_versions()
                if not versions:
                    raise FileNotFoundError("No trained models found in repository")
                version = versions[-1]["version"]

        model_filename = f"model_{version}.joblib"
        meta_filename = f"model_{version}.meta.json"
        model_path = os.path.join(self.model_dir, model_filename)
        meta_path = os.path.join(self.model_dir, meta_filename)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model version '{version}' not found at {model_path}")

        # Load model
        start = time.time()
        model_data = joblib.load(model_path)
        load_time = time.time() - start

        # Reconstruct pipeline
        pipeline = MalwareClassificationPipeline()
        pipeline.preprocessor = model_data["preprocessor"]
        pipeline.classifier = model_data["classifier"]
        pipeline._is_trained = True

        # Load metadata
        metadata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                metadata = json.load(f)
            pipeline._training_metadata = metadata.get("training_metadata", {})

        self._active_pipeline = pipeline
        self._active_version = version
        self._active_metadata = metadata

        logger.info(f"Model loaded: {version} in {load_time:.3f}s")
        return pipeline

    def get_active_pipeline(self) -> Optional[MalwareClassificationPipeline]:
        """Return the currently loaded pipeline, loading if needed."""
        if self._active_pipeline is None:
            try:
                self.load_model()
            except FileNotFoundError:
                return None
        return self._active_pipeline

    def list_versions(self) -> List[Dict[str, Any]]:
        """List all available model versions with metadata."""
        versions = []
        for filename in sorted(os.listdir(self.model_dir)):
            if filename.endswith(".meta.json"):
                meta_path = os.path.join(self.model_dir, filename)
                try:
                    with open(meta_path, "r") as f:
                        meta = json.load(f)
                    model_path = os.path.join(self.model_dir, meta.get("model_filename", ""))
                    meta["file_exists"] = os.path.exists(model_path)
                    if meta["file_exists"]:
                        meta["file_size_bytes"] = os.path.getsize(model_path)
                    versions.append(meta)
                except Exception as e:
                    logger.warning(f"Failed to read metadata {filename}: {e}")

        return versions

    def delete_version(self, version: str) -> bool:
        """Delete a specific model version."""
        model_path = os.path.join(self.model_dir, f"model_{version}.joblib")
        meta_path = os.path.join(self.model_dir, f"model_{version}.meta.json")

        deleted = False
        for path in [model_path, meta_path]:
            if os.path.exists(path):
                os.remove(path)
                deleted = True

        if self._active_version == version:
            self._active_pipeline = None
            self._active_version = None
            self._active_metadata = None
            # Remove stale active_model.json to prevent crash on restart
            active_path = os.path.join(self.model_dir, "active_model.json")
            if os.path.exists(active_path):
                os.remove(active_path)
                logger.info(f"Cleared active model pointer (deleted version: {version})")

        return deleted

    def _set_active_version(self, version: str, metadata: Dict[str, Any]):
        """Mark a version as active."""
        active_path = os.path.join(self.model_dir, "active_model.json")
        with open(active_path, "w") as f:
            json.dump({"version": version, "set_at": datetime.now(timezone.utc).isoformat()}, f)
        self._active_version = version
        self._active_metadata = metadata

    def _get_active_version(self) -> Optional[str]:
        """Read the active model version."""
        active_path = os.path.join(self.model_dir, "active_model.json")
        if os.path.exists(active_path):
            with open(active_path, "r") as f:
                data = json.load(f)
            return data.get("version")
        return None


# ─── Global Repository Singleton ─────────────────────────────────────

_repository: Optional[ModelRepository] = None
_repository_lock = threading.Lock()


def get_model_repository() -> ModelRepository:
    """Get the global model repository instance (thread-safe)."""
    global _repository
    if _repository is None:
        with _repository_lock:
            # Double-check after acquiring lock
            if _repository is None:
                _repository = ModelRepository()
    return _repository
