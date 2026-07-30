"""
ThreatLens AI — Model Validation
Comprehensive model evaluation, metrics computation, and comparison.

Implements the VALIDATION box from the architecture diagram.
"""

import logging
from typing import Dict, Any, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)

from app.ml.model_pipeline import INDEX_TO_CLASS, MALWARE_CLASSES

logger = logging.getLogger("threatlens.ml.validation")


class ModelEvaluator:
    """
    Comprehensive model evaluation suite.

    Generates accuracy, precision, recall, F1, confusion matrix,
    per-class metrics, and ROC-AUC scores.
    """

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
        class_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run full evaluation.

        Parameters
        ----------
        y_true : np.ndarray
            Ground truth labels (integer indices)
        y_pred : np.ndarray
            Predicted labels (integer indices)
        y_proba : np.ndarray, optional
            Predicted probabilities (n_samples, n_classes) for ROC-AUC
        class_names : list of str, optional
            Human-readable class names

        Returns
        -------
        dict
            Comprehensive evaluation results
        """
        if class_names is None:
            unique_classes = sorted(np.unique(np.concatenate([y_true, y_pred])))
            class_names = [INDEX_TO_CLASS.get(int(c), f"Class_{c}") for c in unique_classes]

        results: Dict[str, Any] = {}

        # ─── Overall Metrics ──────────────────────────────────────
        results["accuracy"] = round(float(accuracy_score(y_true, y_pred)), 4)
        results["precision_macro"] = round(float(
            precision_score(y_true, y_pred, average="macro", zero_division=0)
        ), 4)
        results["recall_macro"] = round(float(
            recall_score(y_true, y_pred, average="macro", zero_division=0)
        ), 4)
        results["f1_macro"] = round(float(
            f1_score(y_true, y_pred, average="macro", zero_division=0)
        ), 4)
        results["precision_weighted"] = round(float(
            precision_score(y_true, y_pred, average="weighted", zero_division=0)
        ), 4)
        results["recall_weighted"] = round(float(
            recall_score(y_true, y_pred, average="weighted", zero_division=0)
        ), 4)
        results["f1_weighted"] = round(float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ), 4)

        # ─── Per-Class Metrics ────────────────────────────────────
        per_class_precision = precision_score(
            y_true, y_pred, average=None, zero_division=0
        )
        per_class_recall = recall_score(
            y_true, y_pred, average=None, zero_division=0
        )
        per_class_f1 = f1_score(
            y_true, y_pred, average=None, zero_division=0
        )

        per_class = []
        unique_labels = sorted(np.unique(np.concatenate([y_true, y_pred])))
        for i, label in enumerate(unique_labels):
            class_name = INDEX_TO_CLASS.get(int(label), f"Class_{label}")
            support = int(np.sum(y_true == label))
            per_class.append({
                "class": class_name,
                "label": int(label),
                "precision": round(float(per_class_precision[i]), 4),
                "recall": round(float(per_class_recall[i]), 4),
                "f1_score": round(float(per_class_f1[i]), 4),
                "support": support,
            })

        results["per_class_metrics"] = per_class

        # ─── Confusion Matrix ─────────────────────────────────────
        cm = confusion_matrix(y_true, y_pred)
        results["confusion_matrix"] = {
            "matrix": cm.tolist(),
            "labels": [INDEX_TO_CLASS.get(int(l), f"Class_{l}") for l in unique_labels],
        }

        # ─── ROC-AUC (if probabilities available) ─────────────────
        if y_proba is not None:
            try:
                if y_proba.shape[1] == 2:
                    auc = roc_auc_score(y_true, y_proba[:, 1])
                else:
                    auc = roc_auc_score(
                        y_true, y_proba,
                        multi_class="ovr",
                        average="weighted",
                    )
                results["roc_auc_weighted"] = round(float(auc), 4)
            except Exception as e:
                logger.warning(f"ROC-AUC calculation failed: {e}")
                results["roc_auc_weighted"] = None

        # ─── Summary ─────────────────────────────────────────────
        results["n_samples"] = int(len(y_true))
        results["n_classes"] = int(len(unique_labels))

        logger.info(
            f"Evaluation: Accuracy={results['accuracy']:.4f} | "
            f"F1(weighted)={results['f1_weighted']:.4f} | "
            f"AUC={results.get('roc_auc_weighted', 'N/A')}"
        )

        return results


def compare_models(
    evaluations: List[Dict[str, Any]],
    model_names: List[str],
) -> Dict[str, Any]:
    """
    Compare multiple model evaluations side by side.

    Parameters
    ----------
    evaluations : list of evaluation result dicts
    model_names : list of model version names

    Returns
    -------
    dict with comparison table and best model info
    """
    comparison = []
    for name, eval_result in zip(model_names, evaluations):
        comparison.append({
            "model": name,
            "accuracy": eval_result.get("accuracy"),
            "f1_weighted": eval_result.get("f1_weighted"),
            "precision_weighted": eval_result.get("precision_weighted"),
            "recall_weighted": eval_result.get("recall_weighted"),
            "roc_auc": eval_result.get("roc_auc_weighted"),
            "n_samples": eval_result.get("n_samples"),
        })

    # Find best model by F1 score
    best_idx = max(
        range(len(comparison)),
        key=lambda i: comparison[i].get("f1_weighted", 0) or 0,
    )

    return {
        "comparison_table": comparison,
        "best_model": {
            "name": model_names[best_idx],
            "metric": "f1_weighted",
            "value": comparison[best_idx].get("f1_weighted"),
        },
    }
