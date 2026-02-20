import logging
import os
import pickle
from typing import Any

import numpy as np

try:
    import joblib
except Exception:  # joblib not available at import time
    joblib = None

from .model_adapter import DatasetAdapter, ModelAdapter, SklearnModelAdapter
from .rf_dataset_adapter import RandomForestDatasetAdapter

try:
    from .config_based_adapter import load_dataset_adapter_from_config
except ImportError:
    load_dataset_adapter_from_config = None

logger = logging.getLogger(__name__)

# Probability clipping bounds to prevent overconfidence
# Medical AI should avoid 0% and 100% certainty
PROB_CLIP_MIN = 0.01  # Minimum 1% probability
PROB_CLIP_MAX = 0.99  # Maximum 99% probability


def clip_probabilities(
    probs: np.ndarray, min_val: float = PROB_CLIP_MIN, max_val: float = PROB_CLIP_MAX
) -> np.ndarray:
    """Clip probabilities to avoid overconfidence.

    In medical AI, predicting 0% or 100% certainty is problematic because:
    1. It implies impossible certainty that doesn't exist in medicine
    2. It can lead to overconfident clinical decisions
    3. It indicates poor model calibration

    Args:
        probs: Array of probabilities
        min_val: Minimum probability (default 0.01 = 1%)
        max_val: Maximum probability (default 0.99 = 99%)

    Returns:
        Clipped probability array
    """
    return np.clip(probs, min_val, max_val)


# Path to the model file.
# Switched from LogisticRegression to Random Forest (Feb 2026).
# The RF model is more appropriate for SHAP TreeExplainer than explaining
# an intrinsically-interpretable linear model with a linear explainer.
MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "../models/random_forest_final.pkl"),
)

# ---------------------------------------------------------------------------
# Module-level model cache
# ---------------------------------------------------------------------------
# Deserializing the Random Forest pickle more than once in the same process
# can trigger a SIGABRT (e.g. due to concurrent LLVM/numba initialisation
# from SHAP while an asyncio event-loop thread is running).  Caching the
# model object here ensures that only the first ``ModelWrapper`` instance
# actually reads from disk; subsequent instances share the same object.
_MODEL_CACHE: dict[str, Any] = {}


class ModelWrapper:
    def __init__(
        self,
        model_adapter: ModelAdapter | None = None,
        dataset_adapter: DatasetAdapter | None = None,
    ):
        """Initialize ModelWrapper with optional adapters.

        Args:
            model_adapter: Adapter for model framework (sklearn, PyTorch, etc.)
                          If None, auto-detected when model is loaded
            dataset_adapter: Adapter for dataset preprocessing
                            If None, defaults to RandomForestDatasetAdapter
        """
        self.model: Any | None = None
        self.model_adapter: ModelAdapter | None = model_adapter
        self.dataset_adapter: DatasetAdapter = (
            dataset_adapter or RandomForestDatasetAdapter()
        )
        # retain path for diagnostics
        self.model_path = MODEL_PATH
        # Attempt to load at construction but do NOT raise — keep app import-safe.
        try:
            self.load_model()
        except Exception as e:
            logger.exception("Model load failed during ModelWrapper init: %s", e)
            self.model = None

    @classmethod
    def from_config(
        cls,
        config_path: str,
        model_adapter: ModelAdapter | None = None,
        model_path: str | None = None,
    ) -> "ModelWrapper":
        """Create ModelWrapper with config-based dataset adapter.

        This is the recommended approach for maximum flexibility.
        Instead of hardcoding feature engineering in Python, define
        features in a JSON configuration file.

        Args:
            config_path: Path to feature configuration JSON file
            model_adapter: Optional model adapter (auto-detected if None)
            model_path: Optional model file path (uses MODEL_PATH env var if None)

        Returns:
            ModelWrapper instance with config-based dataset adapter

        Example:
            >>> wrapper = ModelWrapper.from_config("config/random_forest_features.json")
            >>> X = wrapper.prepare_input({"age": 45, "gender": "w"})
            >>> prediction = wrapper.predict({"age": 45, "gender": "w"})
        """
        if load_dataset_adapter_from_config is None:
            raise ImportError(
                "config_based_adapter module not available. "
                "Cannot create ModelWrapper from config."
            )

        dataset_adapter = load_dataset_adapter_from_config(config_path)

        # Temporarily set MODEL_PATH if provided
        if model_path:
            original_path = os.environ.get("MODEL_PATH")
            os.environ["MODEL_PATH"] = model_path
            try:
                wrapper = cls(
                    model_adapter=model_adapter,
                    dataset_adapter=dataset_adapter,
                )
            finally:
                if original_path:
                    os.environ["MODEL_PATH"] = original_path
                else:
                    os.environ.pop("MODEL_PATH", None)
        else:
            wrapper = cls(
                model_adapter=model_adapter,
                dataset_adapter=dataset_adapter,
            )

        return wrapper

    # ------------------------------------------------------------------
    # Model metadata helpers
    # ------------------------------------------------------------------
    def get_model_type_name(self) -> str:
        """Return a human-readable name for the loaded model type."""
        if self.model is None:
            return "Unknown"
        return type(self.model).__name__

    def get_n_features(self) -> int | None:
        """Return the number of input features the model expects."""
        if self.model is not None and hasattr(self.model, "n_features_in_"):
            return int(self.model.n_features_in_)
        return (
            len(self.dataset_adapter.get_feature_names())
            if self.dataset_adapter
            else None
        )

    # Compatibility wrapper: older code expects `load()` and `is_loaded()`
    def load(self) -> None:
        return self.load_model()

    def is_loaded(self) -> bool:
        return self.model is not None

    def _auto_detect_model_adapter(self) -> ModelAdapter:
        """Auto-detect the appropriate model adapter based on model type.

        Returns:
            ModelAdapter instance for the detected framework
        """
        if self.model is None:
            raise RuntimeError("No model loaded")

        # Check for sklearn
        try:
            import sklearn.base

            if isinstance(self.model, sklearn.base.BaseEstimator) or hasattr(
                self.model, "predict"
            ):
                logger.info("Auto-detected sklearn model, using SklearnModelAdapter")
                return SklearnModelAdapter(self.model)
        except ImportError:
            pass

        # Check for PyTorch (placeholder for future)
        # try:
        #     import torch
        #     if isinstance(self.model, torch.nn.Module):
        #         return PyTorchModelAdapter(self.model)
        # except ImportError:
        #     pass

        # Default to sklearn adapter (most permissive)
        logger.warning(
            f"Could not auto-detect model type for {type(self.model).__name__}, "
            "defaulting to SklearnModelAdapter"
        )
        return SklearnModelAdapter(self.model)

    def load_model(self) -> None:
        """Try to load the model using joblib (preferred) then pickle as fallback.

        This method raises exceptions to the caller; the constructor catches them
        and leaves `self.model` as None so the application can continue to start.
        """
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

        # Return cached model if already loaded (avoids SIGABRT from double-
        # deserialization of tree-based sklearn models in threaded contexts).
        resolved = os.path.realpath(MODEL_PATH)
        if resolved in _MODEL_CACHE:
            self.model = _MODEL_CACHE[resolved]
            logger.info("Reusing cached model for %s", MODEL_PATH)
        else:
            # Prefer joblib if available and the file looks like a joblib dump
            if joblib is not None:
                try:
                    self.model = joblib.load(MODEL_PATH)
                    logger.info("Loaded model with joblib from %s", MODEL_PATH)
                except Exception:
                    logger.debug(
                        "joblib.load failed, will try pickle.load", exc_info=True
                    )
                    # Fallback to pickle
                    with open(MODEL_PATH, "rb") as f:
                        self.model = pickle.load(f)
                        logger.info("Loaded model with pickle from %s", MODEL_PATH)
            else:
                # Fallback to pickle
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                    logger.info("Loaded model with pickle from %s", MODEL_PATH)

            # Cache for subsequent ModelWrapper instances
            _MODEL_CACHE[resolved] = self.model

        # Auto-detect model adapter if not provided
        if self.model_adapter is None:
            self.model_adapter = self._auto_detect_model_adapter()

    def predict(self, raw: dict, clip: bool = True):
        """Return predicted probability for class 1.

        The raw dict is transformed by the dataset adapter before prediction.
        If no model is loaded a RuntimeError is raised so the API route can
        decide on a fallback behaviour.

        Args:
            raw: Patient data dictionary or preprocessed feature array
            clip: If True, clip probabilities to [0.01, 0.99] to avoid overconfidence

        Returns:
            Array of predicted probabilities (clipped if clip=True)
        """
        if self.model is None:
            raise RuntimeError("No model loaded")
        if self.model_adapter is None:
            raise RuntimeError("No model adapter configured")

        # Accept either raw dict-like input or already-preprocessed X (DataFrame/array)
        if isinstance(raw, dict) or hasattr(raw, "get"):
            X = self.prepare_input(raw)
        else:
            X = raw

        # Use model adapter for prediction
        probs = self.model_adapter.predict_proba(X)

        # Extract positive class probability (column 1) if 2D
        if probs.ndim == 2:
            probs = probs[:, 1]

        return clip_probabilities(probs) if clip else probs

    def predict_with_confidence(
        self, raw: dict, confidence_level: float = 0.95
    ) -> dict:
        """Return prediction with confidence interval.

        For Random Forest models, confidence intervals are estimated from the
        variance of individual tree predictions (much more principled than the
        logistic-regression heuristic that was used before).

        For other model types, falls back to a heuristic based on prediction
        distance from the decision boundary (0.5).

        Args:
            raw: Patient data dictionary
            confidence_level: Confidence level for interval (default 0.95 = 95%)

        Returns:
            Dictionary with:
            - prediction: Point estimate (clipped probability)
            - confidence_interval: (lower, upper) bounds
            - uncertainty: Width of confidence interval (higher = more uncertain)
        """
        from scipy import stats

        if self.model is None:
            raise RuntimeError("No model loaded")

        X = self.prepare_input(raw)

        # Get point estimate
        prob = self.predict(raw, clip=True)
        if hasattr(prob, "__len__"):
            prob = prob[0]

        # --- Tree ensemble: use variance of individual tree predictions ---
        if hasattr(self.model, "estimators_"):
            # Collect predictions from each tree
            tree_probs = []
            for tree in self.model.estimators_:
                p = tree.predict_proba(X)
                if p.ndim == 2 and p.shape[1] >= 2:
                    tree_probs.append(p[0, 1])
                else:
                    tree_probs.append(float(p[0]))
            tree_probs = np.array(tree_probs)
            std = tree_probs.std()
            z_score = stats.norm.ppf((1 + confidence_level) / 2)
            half_width = z_score * std
        else:
            # Heuristic fallback for non-ensemble models
            dist_from_uncertain = abs(prob - 0.5)
            base_uncertainty = 0.10
            uncertainty_factor = 1.0 - (dist_from_uncertain * 0.8)
            z_score = stats.norm.ppf((1 + confidence_level) / 2)
            half_width = z_score * base_uncertainty * uncertainty_factor

        lower = max(PROB_CLIP_MIN, prob - half_width)
        upper = min(PROB_CLIP_MAX, prob + half_width)

        return {
            "prediction": float(prob),
            "confidence_interval": (float(lower), float(upper)),
            "uncertainty": float(upper - lower),
            "confidence_level": confidence_level,
        }

    def prepare_input(self, raw: dict):
        """Prepare a single-row input suitable for the loaded model.

        Uses the dataset adapter to convert raw patient dict to the
        feature array expected by the model.

        Args:
            raw: Raw input dictionary

        Returns:
            Preprocessed feature array
        """
        return self.dataset_adapter.preprocess(raw)

    def get_feature_names(self) -> list[str]:
        """Get the list of feature names expected by the model.

        Returns:
            List of feature names in the correct order
        """
        return self.dataset_adapter.get_feature_names()
