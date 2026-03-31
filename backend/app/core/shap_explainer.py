"""SHAP explanation wrapper for model interpretability.

Provides SHAP-based feature importance explanations for predictions.
The primary explainer is TreeExplainer (fast, exact) for the Random Forest
model.  LinearExplainer and KernelExplainer are retained as fallbacks for
alternative model types.
"""

from __future__ import annotations

import base64
import io
import logging
import os
from typing import Any

import numpy as np
import pandas as pd

# Prevent OpenMP threading conflicts that can cause SIGABRT when SHAP's
# TreeExplainer runs alongside an asyncio event-loop thread (e.g. in tests
# using FastAPI TestClient).  Setting these **before** SHAP/scikit-learn
# import their C extensions is the safest approach.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

logger = logging.getLogger(__name__)


class ShapExplainer:
    """Wrapper for SHAP explanations with support for linear and tree-based models.

    This class provides:
    - Feature importance values (SHAP values) for individual predictions
    - Optional visualization as base64-encoded plots
    - Automatic explainer selection based on model type
    """

    def __init__(
        self,
        model: Any,
        feature_names: list[str] | None = None,
        background_data: Any | None = None,
        use_transformed: bool = True,
    ):
        """
        Initialize SHAP explainer.

        Args:
            model: Trained model (Pipeline or estimator)
            feature_names: Feature names (if None, extracted from model)
            background_data: Background samples - should be TRANSFORMED if use_transformed=True
            use_transformed: If True, work on transformed features (recommended for pipelines)
        """
        self.model = model
        self.feature_names = feature_names
        self.explainer: Any = None
        self.use_transformed = use_transformed
        self._final_estimator = None
        self._preprocessor = None
        # Maps for categorical encoding when background is a DataFrame
        self._value_to_code: dict[str, dict[Any, int]] = {}
        self._code_to_value: dict[str, dict[int, Any]] = {}
        self._cat_columns: list[str] = []
        # Flag indicating that we encoded categorical columns to numeric codes
        self._masker_numeric = False

        # Lazy import
        try:
            import shap

            self._shap = shap
        except ImportError:
            logger.warning("SHAP not installed. Install with: pip install shap")
            self._shap = None
            return

        # Extract final estimator and preprocessor if pipeline
        if hasattr(model, "named_steps"):
            # Check for common preprocessor step names
            self._preprocessor = (
                model.named_steps.get("preprocessor")
                or model.named_steps.get("scaler")
                or model.named_steps.get("transformer")
                or model.named_steps.get("preprocessing")
            )
            # If no named preprocessor found but there are multiple steps,
            # treat all steps except the last as the preprocessor
            if self._preprocessor is None and len(model.steps) > 1:
                # Create a pipeline from all but the last step for transformation
                from sklearn.pipeline import Pipeline as SkPipeline

                preprocessing_steps = model.steps[:-1]
                if preprocessing_steps:
                    self._preprocessor = SkPipeline(preprocessing_steps)
            # Final estimator is last step
            self._final_estimator = model.steps[-1][1] if model.steps else model
        else:
            self._final_estimator = model

        # If feature_names not provided, try to extract
        if self.feature_names is None:
            self.feature_names = self._extract_feature_names()

        # Initialize explainer
        try:
            # If background_data is a pandas DataFrame, prefer to prepare it
            # (encode categorical cols deterministically and transform to numeric)
            if isinstance(background_data, pd.DataFrame):
                transformed_bg = self._prepare_background_and_transform(background_data)
            elif (
                background_data is not None
                and self._preprocessor is not None
                and use_transformed
            ):
                # Transform numpy array background data through preprocessor
                try:
                    transformed_bg = self._preprocessor.transform(background_data)
                    logger.info("Transformed background data through preprocessor")
                except Exception as e:
                    logger.warning("Failed to transform background data: %s", e)
                    transformed_bg = background_data
            else:
                transformed_bg = background_data

            # For simple models (non-pipeline), always use raw features
            # For pipeline models with preprocessor, use transformed features
            if use_transformed and self._preprocessor is not None:
                # Work on transformed features (avoids dtype issues)
                self._init_transformed_explainer(transformed_bg)
            else:
                # Work on raw features (works for simple models and pipelines without preprocessor)
                self._init_raw_explainer(transformed_bg)
        except Exception as exc:
            logger.exception("Failed to initialize SHAP explainer: %s", exc)
            self.explainer = None

    def _prepare_background_and_transform(
        self, raw_df: pd.DataFrame
    ) -> np.ndarray | None:
        """Encode categorical columns deterministically and transform using pipeline preprocessor.

        Returns transformed numpy array suitable for SHAP explainers.
        """
        df = raw_df.copy()
        # Identify categorical/object columns (keep original strings initially)
        cat_cols: list[str] = [
            c
            for c in df.columns
            if df[c].dtype == object or isinstance(df[c].dtype, pd.CategoricalDtype)
        ]
        self._cat_columns = cat_cols

        # First try to transform raw DataFrame as-is (preprocessor likely expects strings)
        if self.use_transformed and self._preprocessor is not None:
            try:
                transformed = self._preprocessor.transform(df)
                # We keep masker_numeric False because masker will operate on numeric transformed data
                self._masker_numeric = False
                return transformed
            except Exception as e:
                logger.info(
                    "Preprocessor.transform failed on raw background (will try encoded fallback): %s",
                    e,
                )

        # If transform failed or no preprocessor, create deterministic encodings for categorical cols
        for col in cat_cols:
            uniques = sorted([str(x) for x in df[col].dropna().unique()])
            v2c = {v: i for i, v in enumerate(uniques)}
            c2v = {i: v for v, i in v2c.items()}
            # Store mappings
            self._value_to_code[col] = v2c
            self._code_to_value[col] = c2v
            # Map values; unseen values -> -1
            # Use default argument to capture v2c in closure
            df[col] = (
                df[col]
                .astype(object)
                .apply(lambda x, mapping=v2c: mapping.get(str(x), -1))
            )

        # Mark that we've encoded the masker to numeric (fallback)
        self._masker_numeric = len(cat_cols) > 0

        # If we have a preprocessor, try to transform encoded df
        if self.use_transformed and self._preprocessor is not None:
            try:
                transformed = self._preprocessor.transform(df)
                return transformed
            except Exception as e:
                logger.warning(
                    "Preprocessor.transform failed on encoded background as well: %s", e
                )
                try:
                    return df.values
                except Exception:
                    return None

        # No preprocessor: return numeric numpy array (encoded or original)
        try:
            return df.values
        except Exception:
            return None

    def _extract_feature_names(self) -> list | None:
        """Extract feature names from model."""
        try:
            # Try preprocessor first
            if self._preprocessor and hasattr(
                self._preprocessor, "get_feature_names_out"
            ):
                return list(self._preprocessor.get_feature_names_out())
            # Try model directly
            if hasattr(self.model, "feature_names_in_"):
                return list(self.model.feature_names_in_)
        except Exception:
            pass
        return None

    def _init_transformed_explainer(self, background_data: np.ndarray | None):
        """Initialize explainer on transformed features.

        This is the recommended path for pipelines: SHAP works on numeric
        transformed features, avoiding all dtype/masker issues.
        """
        shap = self._shap
        estimator = self._final_estimator

        # If no background data provided, generate appropriate zeros
        try:
            n_features = int(self._get_n_features())
        except (TypeError, ValueError):
            n_features = 0
        if background_data is None:
            if n_features > 0:
                background_data = np.zeros((1, n_features))
                logger.info(
                    "No background data provided, using zeros with %d features",
                    n_features,
                )
        else:
            # Validate dimensions - mismatch can cause SIGABRT in TreeExplainer C code
            bg_cols = (
                background_data.shape[1]
                if hasattr(background_data, "shape") and background_data.ndim == 2
                else 0
            )
            if n_features > 0 and bg_cols != n_features:
                logger.warning(
                    "Background data has %d cols but model expects %d features; "
                    "regenerating zeros",
                    bg_cols,
                    n_features,
                )
                background_data = np.zeros((1, n_features))

        # Use TreeExplainer for tree models (fast and accurate)
        if hasattr(estimator, "feature_importances_") or hasattr(estimator, "tree_"):
            logger.info("Using TreeExplainer on final estimator")
            try:
                # For RandomForest/tree models, use TreeExplainer WITHOUT background data.
                # This enables "path-dependent" SHAP which provides meaningful values
                # for all features, not just zeros for features matching background.
                # Note: With background data = zeros, most features get SHAP = 0
                # because the tree paths are similar when features are zero.
                self.explainer = shap.TreeExplainer(estimator)
                logger.info(
                    "Successfully initialized TreeExplainer (path-dependent, no background)"
                )
                return
            except Exception as e:
                logger.warning("TreeExplainer failed: %s", e)

        # Use LinearExplainer for linear models
        if hasattr(estimator, "coef_"):
            logger.info("Using LinearExplainer on final estimator")
            try:
                # LinearExplainer requires feature_names to be passed during initialization
                if self.feature_names:
                    self.explainer = shap.LinearExplainer(
                        estimator, background_data, feature_names=self.feature_names
                    )
                else:
                    self.explainer = shap.LinearExplainer(estimator, background_data)
                logger.info("Successfully initialized LinearExplainer")
                return
            except Exception as e:
                logger.warning("LinearExplainer failed, will try fallback: %s", e)

        # Fallback: KernelExplainer (slower but works for any model)
        logger.info("Using KernelExplainer on final estimator")
        predict_fn = (
            estimator.predict_proba  # type: ignore[union-attr]
            if hasattr(estimator, "predict_proba")
            else estimator.predict  # type: ignore[union-attr]
        )

        try:
            self.explainer = shap.KernelExplainer(predict_fn, background_data)
            logger.info("Successfully initialized KernelExplainer")
        except Exception as e:
            logger.error("Failed to initialize any SHAP explainer: %s", e)
            self.explainer = None

    def _init_raw_explainer(self, background_data: np.ndarray | None):
        """Initialize explainer on raw features (legacy/fallback path)."""
        shap = self._shap

        # If no background data provided, generate appropriate zeros
        # Determine which estimator to use for explainer (prefer final estimator for pipelines)
        estimator = (
            self._final_estimator if self._final_estimator is not None else self.model
        )

        try:
            n_features = int(self._get_n_features())
        except (TypeError, ValueError):
            n_features = 0
        if background_data is None:
            if n_features > 0:
                background_data = np.zeros((1, n_features))
                logger.info(
                    "No background data provided, using zeros with %d features",
                    n_features,
                )
        else:
            # Validate dimensions - mismatch can cause SIGABRT in TreeExplainer C code
            bg_cols = (
                background_data.shape[1]
                if hasattr(background_data, "shape") and background_data.ndim == 2
                else 0
            )
            if n_features > 0 and bg_cols != n_features:
                logger.warning(
                    "Background data has %d cols but model expects %d features; "
                    "regenerating zeros",
                    bg_cols,
                    n_features,
                )
                background_data = np.zeros((1, n_features))

        # Use TreeExplainer for tree models (fast and accurate)
        if hasattr(estimator, "feature_importances_") or hasattr(estimator, "tree_"):
            logger.info("Using TreeExplainer on estimator")
            try:
                # Use TreeExplainer WITHOUT background data for "path-dependent" SHAP.
                # This provides meaningful values for all features.
                # Using zeros background causes most features to get SHAP = 0.
                self.explainer = shap.TreeExplainer(estimator)
                logger.info(
                    "Successfully initialized TreeExplainer (path-dependent, no background)"
                )
                return
            except Exception as e:
                logger.warning("TreeExplainer failed: %s", e)

        # For linear models, use LinearExplainer (faster and more accurate)
        if hasattr(estimator, "coef_"):
            logger.info("Using LinearExplainer for linear model")
            try:
                if self.feature_names:
                    self.explainer = shap.LinearExplainer(
                        estimator, background_data, feature_names=self.feature_names
                    )
                else:
                    self.explainer = shap.LinearExplainer(estimator, background_data)
                logger.info("Successfully initialized LinearExplainer")
                return
            except Exception as e:
                logger.warning("LinearExplainer failed: %s", e)

        # Try unified API with original model (may work better with pipelines)
        try:
            self.explainer = shap.Explainer(self.model, background_data)
            logger.info("Using shap.Explainer (unified API)")
            return
        except Exception as e:
            logger.debug("Unified Explainer failed: %s", e)

        # Fallback to KernelExplainer
        logger.info("Using KernelExplainer on full model")
        predict_fn = (
            self.model.predict_proba
            if hasattr(self.model, "predict_proba")
            else self.model.predict
        )

        try:
            self.explainer = shap.KernelExplainer(predict_fn, background_data)
            logger.info("Successfully initialized KernelExplainer")
        except Exception as e:
            logger.error("Failed to initialize any SHAP explainer: %s", e)
            self.explainer = None

    def _get_n_features(self) -> int:
        """Get number of features expected by model."""
        if hasattr(self.model, "n_features_in_"):
            return self.model.n_features_in_
        if hasattr(self.model, "coef_"):
            coef = self.model.coef_
            return coef.shape[1] if coef.ndim > 1 else len(coef)
        if self.feature_names:
            return len(self.feature_names)
        # Last resort fallback
        return 10

    def explain(
        self,
        sample: np.ndarray,
        return_plot: bool = False,
    ) -> dict[str, Any]:
        """Generate SHAP explanation for a single prediction.

        Args:
            sample: Input sample (1D or 2D array)
            return_plot: If True, include base64-encoded waterfall plot

        Returns:
            Dictionary with:
            - feature_importance: Dict mapping feature names to SHAP values
            - shap_values: Raw SHAP values as list
            - base_value: Expected value (baseline)
            - plot_base64: Optional base64-encoded plot
        """
        if self._shap is None or self.explainer is None:
            logger.warning("SHAP explainer not available, returning empty explanation")
            return {"feature_importance": {}, "shap_values": [], "base_value": 0.0}

        # Ensure 2D array
        if sample.ndim == 1:
            sample = sample.reshape(1, -1)

        # If we're using transformed features and have a preprocessor, transform the sample
        sample_for_explainer = sample
        if self.use_transformed and self._preprocessor is not None:
            try:
                sample_for_explainer = self._preprocessor.transform(sample)
                logger.debug(
                    "Transformed sample through preprocessor for SHAP explanation"
                )
            except Exception as e:
                logger.warning("Failed to transform sample for SHAP: %s", e)
                sample_for_explainer = sample

        try:
            # Compute SHAP values. Different SHAP versions and explainers expose
            # values in different ways (shap_values array, or Explanation object),
            # so handle multiple formats.
            shap_vals = None
            base_value = 0.0

            if hasattr(self.explainer, "shap_values"):
                # Traditional API
                shap_values = self.explainer.shap_values(sample_for_explainer)
                if isinstance(shap_values, list):
                    # Multi-class output
                    shap_vals = (
                        shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
                    )
                else:
                    # Single output - may be 1D or 2D array
                    if shap_values.ndim == 2:
                        shap_vals = shap_values[0]  # First sample
                    elif shap_values.ndim == 3:
                        # (n_samples, n_features, n_classes)
                        # Take first sample, and positive class (index 1) if available
                        if shap_values.shape[2] > 1:
                            shap_vals = shap_values[0, :, 1]
                        else:
                            shap_vals = shap_values[0, :, 0]
                    else:
                        shap_vals = shap_values

                if hasattr(self.explainer, "expected_value"):
                    base_value = self.explainer.expected_value
                    if isinstance(base_value, list | np.ndarray):
                        base_value = (
                            base_value[1] if len(base_value) > 1 else base_value[0]
                        )
                    # Ensure float
                    try:
                        base_value = float(base_value)
                    except (TypeError, ValueError):
                        base_value = 0.0

            else:
                # Newer unified API: explainer(...) returns an Explanation object
                try:
                    # Prepare sample for explainer. Accept numeric ndarray, or raw DataFrame/dict.
                    sample_to_pass = sample
                    # If sample is a pandas DataFrame or dict-like, convert/encode/transform as needed
                    if not isinstance(sample, np.ndarray):
                        try:
                            df_sample = pd.DataFrame(sample)
                        except Exception:
                            # Try to coerce 2D array
                            df_sample = pd.DataFrame(sample, columns=self.feature_names)

                        # If we previously encoded categorical values for background (fallback),
                        # apply same encoding to sample
                        if (
                            getattr(self, "_masker_numeric", False)
                            and self._value_to_code
                        ):
                            for col, v2c in self._value_to_code.items():
                                if col in df_sample.columns:
                                    # Use default argument to capture v2c in closure
                                    df_sample[col] = (
                                        df_sample[col]
                                        .astype(object)
                                        .apply(
                                            lambda v, mapping=v2c: mapping.get(
                                                str(v), -1
                                            )
                                        )
                                    )

                        # If we have a preprocessor and we're working on transformed features,
                        # transform the DataFrame now
                        if self.use_transformed and self._preprocessor is not None:
                            try:
                                sample_to_pass = self._preprocessor.transform(df_sample)
                            except Exception:
                                # Fallback to raw values
                                sample_to_pass = df_sample.values
                        else:
                            sample_to_pass = df_sample.values

                    explanation = self.explainer(sample_to_pass)
                    # Explanation.values can be (n_samples, n_features) or (n_classes, n_samples, n_features)
                    vals = getattr(explanation, "values", None)
                    if vals is None:
                        # Some explainers use .shap_values
                        vals = getattr(explanation, "shap_values", None)

                    if vals is not None:
                        # Normalize to 1D for single sample
                        if isinstance(vals, list):
                            # multi-class
                            arr = vals[1] if len(vals) > 1 else vals[0]
                            shap_vals = arr[0]
                        elif hasattr(vals, "ndim") and vals.ndim == 3:
                            # (n_samples, n_features, n_classes)
                            if vals.shape[2] > 1:
                                shap_vals = vals[0, :, 1]
                            else:
                                shap_vals = vals[0, :, 0]
                        elif hasattr(vals, "ndim") and vals.ndim == 2:
                            shap_vals = vals[0]
                        else:
                            shap_vals = vals[0]

                    # Try to extract base value(s)
                    base = getattr(explanation, "base_values", None) or getattr(
                        explanation, "expected_value", None
                    )
                    if base is not None:
                        if isinstance(base, list | np.ndarray):
                            try:
                                base_value = float(base[0])
                            except Exception:
                                base_value = float(np.asarray(base).flatten()[0])
                        else:
                            base_value = float(base)
                except Exception:
                    # Let outer except handle fallback
                    raise

            # If shap_vals is None here, something went wrong earlier and will fall to except
            if shap_vals is None:
                raise RuntimeError("SHAP values could not be computed")

            # Create feature importance dict
            feature_importance = {}
            if self.feature_names:
                for i, name in enumerate(self.feature_names):
                    if i < len(shap_vals):
                        # Handle both scalar and array SHAP values
                        val = shap_vals[i]
                        try:
                            # Try direct float conversion
                            feature_importance[name] = float(val)
                        except (TypeError, ValueError):
                            # If it's an array, take the first element
                            try:
                                feature_importance[name] = float(
                                    val.item() if hasattr(val, "item") else val[0]
                                )
                            except Exception:
                                feature_importance[name] = 0.0
            else:
                for i, val in enumerate(shap_vals):
                    try:
                        feature_importance[f"feature_{i}"] = float(val)
                    except (TypeError, ValueError):
                        try:
                            feature_importance[f"feature_{i}"] = float(
                                val.item() if hasattr(val, "item") else val[0]
                            )
                        except Exception:
                            feature_importance[f"feature_{i}"] = 0.0

            # Convert SHAP values list with robust handling
            converted_shap_values = []
            for v in shap_vals:
                try:
                    converted_shap_values.append(float(v))
                except (TypeError, ValueError):
                    try:
                        converted_shap_values.append(
                            float(v.item() if hasattr(v, "item") else v[0])
                        )
                    except Exception:
                        converted_shap_values.append(0.0)

            result = {
                "feature_importance": feature_importance,
                "shap_values": converted_shap_values,
                "base_value": float(base_value),
            }

            # Optionally generate plot
            if return_plot:
                try:
                    plot_base64 = self._generate_plot(shap_vals, base_value, sample[0])
                    result["plot_base64"] = plot_base64
                except Exception as exc:
                    logger.warning("Failed to generate SHAP plot: %s", exc)

            return result

        except Exception as exc:
            logger.exception("SHAP explanation failed: %s", exc)
            return {
                "feature_importance": {},
                "shap_values": [],
                "base_value": 0.0,
                "error": str(exc),
            }

    def _generate_plot(
        self,
        shap_values: np.ndarray,
        base_value: float,
        sample: np.ndarray,
    ) -> str:
        """Generate base64-encoded waterfall plot.

        Args:
            shap_values: SHAP values for the sample
            base_value: Expected value
            sample: Input sample

        Returns:
            Base64-encoded PNG image
        """
        import matplotlib

        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        # Create explanation object for plotting
        explanation = self._shap.Explanation(
            values=shap_values,
            base_values=base_value,
            data=sample,
            feature_names=self.feature_names,
        )

        # Generate waterfall plot
        fig, ax = plt.subplots(figsize=(10, 6))
        self._shap.plots.waterfall(explanation, show=False)

        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight", dpi=100)
        plt.close(fig)
        buffer.seek(0)

        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{image_base64}"

    def get_top_features(
        self,
        sample: np.ndarray,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Get top K most important features for a prediction.

        Args:
            sample: Input sample
            top_k: Number of top features to return

        Returns:
            List of dicts with 'feature', 'importance', and 'value'
        """
        explanation = self.explain(sample, return_plot=False)
        feature_importance = explanation.get("feature_importance", {})

        # Sort by absolute importance
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        # Get sample values if available
        sample_1d = sample.flatten() if sample.ndim > 1 else sample

        top_features = []
        for _i, (feature, importance) in enumerate(sorted_features[:top_k]):
            feature_dict = {
                "feature": feature,
                "importance": importance,
            }
            # Add feature value if we have it
            if self.feature_names and feature in self.feature_names:
                idx = self.feature_names.index(feature)
                if idx < len(sample_1d):
                    feature_dict["value"] = float(sample_1d[idx])
            top_features.append(feature_dict)

        return top_features
