"""Abstract interface for XAI explainer methods.

This module provides a generic interface for different explainability methods
(SHAP, LIME, Integrated Gradients, Captum, Quantus, etc.) to enable the
framework to work with arbitrary XAI libraries.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class Explanation:
    """Generic explanation result that can be returned by any explainer.

    Attributes:
        feature_importance: Dict mapping feature names to importance scores
        feature_values: Dict mapping feature names to their values in this instance
        base_value: Baseline/expected value (e.g., average model output)
        prediction: Model prediction for this instance
        method: Name of the explanation method used
        metadata: Additional method-specific data (plots, raw values, etc.)
    """

    feature_importance: dict[str, float]
    feature_values: dict[str, float]
    base_value: float
    prediction: float
    method: str
    metadata: dict[str, Any] | None = None


class ExplainerInterface(ABC):
    """Abstract base class for all explainer implementations.

    Different XAI methods (SHAP, LIME, Captum, etc.) should implement this
    interface to be compatible with the framework.
    """

    @abstractmethod
    def explain(
        self,
        model: Any,
        input_data: np.ndarray | dict,
        feature_names: list[str] | None = None,
        **kwargs,
    ) -> Explanation:
        """Generate explanation for a single prediction.

        Args:
            model: The trained model (can be sklearn, PyTorch, TF, etc.)
            input_data: Input features (preprocessed array or raw dict)
            feature_names: Names of features (for display)
            **kwargs: Method-specific parameters

        Returns:
            Explanation object with feature importance and metadata
        """
        raise NotImplementedError

    @abstractmethod
    def get_method_name(self) -> str:
        """Return the name of this explanation method."""
        raise NotImplementedError

    def supports_visualization(self) -> bool:
        """Whether this explainer can generate visualizations.

        Returns:
            True if the explainer can generate plots/charts
        """
        return False

    def generate_visualization(self, explanation: Explanation, **kwargs) -> str | None:
        """Generate a base64-encoded visualization of the explanation.

        Args:
            explanation: The explanation to visualize
            **kwargs: Visualization-specific parameters

        Returns:
            Base64-encoded image string or None if not supported
        """
        return None


class ExplainerFactory:
    """Factory for creating explainer instances based on method name.

    This enables runtime selection of explanation methods without hardcoding
    dependencies on specific XAI libraries.
    """

    _registry: dict[str, type[ExplainerInterface]] = {}

    @classmethod
    def register(cls, method_name: str, explainer_class: type[ExplainerInterface]):
        """Register an explainer implementation.

        Args:
            method_name: Identifier for this method (e.g., "shap", "lime")
            explainer_class: The explainer class to instantiate
        """
        cls._registry[method_name.lower()] = explainer_class

    @classmethod
    def create(cls, method: str, model: Any = None, **kwargs) -> ExplainerInterface:
        """Create an explainer instance.

        Args:
            method: Name of the explanation method to use
            model: Optional model instance (some explainers need it at init)
            **kwargs: Method-specific initialization parameters

        Returns:
            An explainer instance

        Raises:
            ValueError: If the method is not registered
        """
        method_lower = method.lower()
        if method_lower not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unknown explainer method: {method}. Available methods: {available}"
            )

        explainer_class = cls._registry[method_lower]
        return explainer_class(model=model, **kwargs)  # type: ignore[call-arg]

    @classmethod
    def list_available_methods(cls) -> list[str]:
        """List all registered explainer methods.

        Returns:
            List of available method names
        """
        return list(cls._registry.keys())
