"""Abstract interfaces for model and dataset adapters.

This module provides generic interfaces to support arbitrary ML frameworks
(scikit-learn, PyTorch, TensorFlow, ONNX) and arbitrary datasets.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class ModelAdapter(ABC):
    """Abstract adapter for different ML model frameworks.

    Enables the framework to work with sklearn, PyTorch, TensorFlow, ONNX,
    and other model formats without hardcoding framework-specific logic.
    """

    def __init__(self, model: Any):
        """Initialize with a model instance.

        Args:
            model: The trained model (sklearn estimator, PyTorch nn.Module, etc.)
        """
        self.model = model

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions.

        Args:
            X: Input features (preprocessed, shape (n_samples, n_features))

        Returns:
            Predictions as numpy array
        """
        raise NotImplementedError

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Generate probability predictions for classification.

        Args:
            X: Input features (preprocessed)

        Returns:
            Probability array (shape: (n_samples, n_classes) or (n_samples,))
        """
        raise NotImplementedError

    @abstractmethod
    def get_model_type(self) -> str:
        """Return the model framework name.

        Returns:
            String identifier ("sklearn", "pytorch", "tensorflow", "onnx", etc.)
        """
        raise NotImplementedError

    def get_feature_importance(self) -> np.ndarray | None:
        """Get model's feature importance if available.

        Returns:
            Feature importance array or None if not applicable
        """
        return None

    def get_coefficients(self) -> np.ndarray | None:
        """Get model coefficients (for linear models).

        Returns:
            Coefficient array or None if not a linear model
        """
        return None


class SklearnModelAdapter(ModelAdapter):
    """Adapter for scikit-learn models."""

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X)
            # Return class 1 probability for binary classification
            if probs.ndim == 2 and probs.shape[1] == 2:
                return probs[:, 1]
            return probs
        elif hasattr(self.model, "decision_function"):
            # Convert decision function to probabilities using sigmoid
            scores = self.model.decision_function(X)
            return 1 / (1 + np.exp(-scores))
        else:
            # Fallback: return predictions as probabilities
            return self.model.predict(X).astype(float)

    def get_model_type(self) -> str:
        return "sklearn"

    def get_coefficients(self) -> np.ndarray | None:
        """Extract coefficients from linear models."""
        if hasattr(self.model, "coef_"):
            return (
                self.model.coef_[0] if self.model.coef_.ndim > 1 else self.model.coef_
            )
        # For pipelines, check final estimator
        if hasattr(self.model, "steps"):
            final_estimator = self.model.steps[-1][1]
            if hasattr(final_estimator, "coef_"):
                return (
                    final_estimator.coef_[0]
                    if final_estimator.coef_.ndim > 1
                    else final_estimator.coef_
                )
        return None

    def get_feature_importance(self) -> np.ndarray | None:
        """Extract feature importance from tree-based models."""
        if hasattr(self.model, "feature_importances_"):
            return self.model.feature_importances_
        # For pipelines, check final estimator
        if hasattr(self.model, "steps"):
            final_estimator = self.model.steps[-1][1]
            if hasattr(final_estimator, "feature_importances_"):
                return final_estimator.feature_importances_
        return None


class DatasetAdapter(ABC):
    """Abstract adapter for different dataset formats and preprocessing.

    Enables the framework to work with arbitrary tabular datasets without
    hardcoding feature names and preprocessing logic.
    """

    @abstractmethod
    def preprocess(self, raw_input: dict) -> np.ndarray:
        """Preprocess raw input into model-ready features.

        Args:
            raw_input: Dictionary with raw feature values

        Returns:
            Preprocessed feature array (shape: (1, n_features))
        """
        raise NotImplementedError

    @abstractmethod
    def get_feature_names(self) -> list[str]:
        """Get the list of feature names after preprocessing.

        Returns:
            List of feature names in the order expected by the model
        """
        raise NotImplementedError

    @abstractmethod
    def get_feature_schema(self) -> dict[str, Any]:
        """Get the schema defining input features.

        Returns:
            Dictionary describing feature types, allowed values, defaults, etc.
        """
        raise NotImplementedError

    def validate_input(self, raw_input: dict) -> tuple[bool, str | None]:
        """Validate raw input against schema.

        Args:
            raw_input: Dictionary with raw feature values

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Default implementation: accept all inputs
        return True, None


class GenericDatasetAdapter(DatasetAdapter):
    """Generic dataset adapter using configuration.

    This adapter can be configured via a schema definition to support
    arbitrary datasets without code changes.
    """

    def __init__(
        self,
        feature_schema: dict[str, Any],
        preprocessor: Any | None = None,
    ):
        """Initialize with feature schema and optional preprocessor.

        Args:
            feature_schema: Dict defining features (name, type, preprocessing, etc.)
            preprocessor: Optional sklearn-compatible preprocessing pipeline
        """
        self.feature_schema = feature_schema
        self.preprocessor = preprocessor

    def preprocess(self, raw_input: dict) -> np.ndarray:
        """Preprocess using configured schema and preprocessor."""
        # Extract and order features according to schema
        feature_list = self.feature_schema.get("features", [])
        values = []

        for feature in feature_list:
            name = feature["name"]
            aliases = feature.get("aliases", [name])
            default = feature.get("default", 0.0)

            # Try to get value from raw_input using name or aliases
            value = raw_input.get(name)
            if value is None:
                for alias in aliases:
                    if alias in raw_input:
                        value = raw_input[alias]
                        break

            if value is None:
                value = default

            # Type conversion
            if feature["type"] == "numeric":
                values.append(float(value))
            elif feature["type"] == "categorical":
                # For categorical, we'd need one-hot encoding
                # This is simplified; real implementation needs proper encoding
                values.append(value)
            else:
                values.append(value)

        # Apply preprocessor if available
        X = np.array(values).reshape(1, -1)
        if self.preprocessor is not None:
            X = self.preprocessor.transform(X)

        return X

    def get_feature_names(self) -> list[str]:
        """Extract feature names from schema."""
        return [f["name"] for f in self.feature_schema.get("features", [])]

    def get_feature_schema(self) -> dict[str, Any]:
        """Return the configured schema."""
        return self.feature_schema
