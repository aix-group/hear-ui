"""Coefficient-based explainer for linear models.

A simple, fast explainer for linear models that uses coefficients
as feature importance scores. This is an alternative to SHAP/LIME
when you need quick explanations for linear models.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from .explainer_interface import ExplainerInterface, Explanation

logger = logging.getLogger(__name__)


class CoefficientExplainer(ExplainerInterface):
    """Coefficient-based explainer for linear models.

    This explainer uses the model's learned coefficients as feature
    importance scores. For each feature:
        contribution = coefficient * feature_value

    This is fast and interpretable but only works for linear models
    (LogisticRegression, LinearRegression, etc.).
    """

    def __init__(self, model: Any = None, **kwargs):
        """Initialize coefficient explainer.

        Args:
            model: Linear model with coef_ attribute
            **kwargs: Unused, for interface compatibility
        """
        self.model = model

    def explain(
        self,
        model: Any,
        input_data: np.ndarray | dict,
        feature_names: list[str] | None = None,
        **kwargs,
    ) -> Explanation:
        """Generate coefficient-based explanation.

        Args:
            model: Linear model to explain
            input_data: Preprocessed input array
            feature_names: Feature names for display
            **kwargs: Unused

        Returns:
            Explanation with coefficient-based feature importance
        """
        # Convert to array if needed
        if isinstance(input_data, dict):
            raise ValueError(
                "CoefficientExplainer requires preprocessed array input. "
                "Use a DatasetAdapter to preprocess dict inputs first."
            )

        X = input_data if isinstance(input_data, np.ndarray) else np.array(input_data)

        # Ensure 2D
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # Get prediction
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)
            prediction = float(probs[:, 1][0]) if probs.ndim == 2 else float(probs[0])
        else:
            prediction = float(model.predict(X)[0])

        # Extract coefficients
        coefficients = self._get_coefficients(model)

        if coefficients is None:
            raise ValueError(
                f"Model {type(model).__name__} does not have coefficients. "
                "CoefficientExplainer only works with linear models."
            )

        if len(coefficients) != X.shape[1]:
            raise ValueError(
                f"Coefficient count ({len(coefficients)}) does not match "
                f"feature count ({X.shape[1]})"
            )

        # Calculate contributions
        contributions = coefficients * X[0]

        # Build feature dicts
        feature_importance = {}
        feature_values = {}

        for i in range(len(contributions)):
            name = (
                feature_names[i]
                if feature_names and i < len(feature_names)
                else f"feature_{i}"
            )
            feature_importance[name] = float(contributions[i])
            feature_values[name] = float(X[0, i])

        # Get intercept as base value
        base_value = self._get_intercept(model)

        return Explanation(
            feature_importance=feature_importance,
            feature_values=feature_values,
            base_value=base_value,
            prediction=prediction,
            method="coefficient",
            metadata={
                "coefficients": coefficients.tolist(),
                "note": "Importance = coefficient × feature_value",
            },
        )

    def _get_coefficients(self, model: Any) -> np.ndarray | None:
        """Extract coefficients from model.

        Args:
            model: Model instance

        Returns:
            Coefficient array or None
        """
        # Direct coef_ attribute
        if hasattr(model, "coef_"):
            coef = model.coef_
            return coef[0] if coef.ndim > 1 else coef

        # Pipeline: check final estimator
        if hasattr(model, "steps"):
            final_estimator = model.steps[-1][1]
            if hasattr(final_estimator, "coef_"):
                coef = final_estimator.coef_
                return coef[0] if coef.ndim > 1 else coef

        return None

    def _get_intercept(self, model: Any) -> float:
        """Extract intercept from model.

        Args:
            model: Model instance

        Returns:
            Intercept value (0.0 if not available)
        """
        # Direct intercept_ attribute
        if hasattr(model, "intercept_"):
            intercept = model.intercept_
            return float(intercept[0] if hasattr(intercept, "__len__") else intercept)

        # Pipeline: check final estimator
        if hasattr(model, "steps"):
            final_estimator = model.steps[-1][1]
            if hasattr(final_estimator, "intercept_"):
                intercept = final_estimator.intercept_
                return float(
                    intercept[0] if hasattr(intercept, "__len__") else intercept
                )

        return 0.0

    def get_method_name(self) -> str:
        """Return method name."""
        return "coefficient"

    def supports_visualization(self) -> bool:
        """Coefficient explainer does not generate plots."""
        return False


class LIMEExplainer(ExplainerInterface):
    """LIME (Local Interpretable Model-agnostic Explanations) explainer.

    This is a placeholder for LIME integration. LIME can explain any
    model by approximating it locally with an interpretable model.

    Requires: pip install lime
    """

    def __init__(self, model: Any = None, **kwargs):
        """Initialize LIME explainer.

        Args:
            model: Model to explain
            **kwargs: LIME-specific parameters
        """
        self.model = model
        self.lime_explainer = None

        # Try to import LIME
        try:
            from lime.lime_tabular import LimeTabularExplainer

            self.LimeTabularExplainer = LimeTabularExplainer
        except ImportError:
            logger.warning("LIME not installed. Install with: pip install lime")
            self.LimeTabularExplainer = None

    def explain(
        self,
        model: Any,
        input_data: np.ndarray | dict,
        feature_names: list[str] | None = None,
        **kwargs,
    ) -> Explanation:
        """Generate LIME explanation.

        Args:
            model: Model to explain
            input_data: Input instance
            feature_names: Feature names
            **kwargs: LIME parameters (training_data, num_features, etc.)

        Returns:
            Explanation with LIME feature importance
        """
        if self.LimeTabularExplainer is None:
            raise ImportError("LIME is not installed. Install with: pip install lime")

        # Convert to array
        if isinstance(input_data, dict):
            raise ValueError(
                "LIMEExplainer requires preprocessed array input. "
                "Use a DatasetAdapter to preprocess dict inputs first."
            )

        X = input_data if isinstance(input_data, np.ndarray) else np.array(input_data)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # Get prediction
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)
            prediction = float(probs[:, 1][0]) if probs.ndim == 2 else float(probs[0])
        else:
            prediction = float(model.predict(X)[0])

        # Initialize LIME explainer if needed
        if self.lime_explainer is None:
            training_data = kwargs.get("training_data")
            if training_data is None:
                # Use the input as a single-sample training set (not ideal)
                training_data = X

            self.lime_explainer = self.LimeTabularExplainer(
                training_data=training_data,
                feature_names=feature_names,
                mode="classification"
                if hasattr(model, "predict_proba")
                else "regression",
            )

        # Generate explanation
        explanation = self.lime_explainer.explain_instance(  # type: ignore[attr-defined]
            data_row=X[0],
            predict_fn=model.predict_proba
            if hasattr(model, "predict_proba")
            else model.predict,
            num_features=kwargs.get("num_features", X.shape[1]),
        )

        # Extract feature importance
        lime_features = explanation.as_list()
        feature_importance = dict(lime_features)

        # Build feature values dict
        feature_values = {}
        if feature_names and X.shape[1] == len(feature_names):
            feature_values = dict(zip(feature_names, X[0], strict=False))
        else:
            feature_values = {f"feature_{i}": val for i, val in enumerate(X[0])}

        return Explanation(
            feature_importance=feature_importance,
            feature_values=feature_values,
            base_value=explanation.intercept[1]
            if hasattr(explanation, "intercept")
            else 0.0,
            prediction=prediction,
            method="lime",
            metadata={"lime_explanation": explanation},
        )

    def get_method_name(self) -> str:
        """Return method name."""
        return "lime"

    def supports_visualization(self) -> bool:
        """LIME supports HTML-based visualizations."""
        return True
