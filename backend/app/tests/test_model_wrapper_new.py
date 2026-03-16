"""Additional tests targeting specific uncovered lines in model_wrapper.py.

Covers:
- from_config classmethod (lines 124-152)
- get_model_type_name (lines 159-161)
- get_n_features (lines 165-167)
- predict_with_confidence tree-ensemble path (lines 331-335)
- predict_with_confidence heuristic fallback (lines 342-346)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.core.model_wrapper import ModelWrapper


class TestFromConfig:
    """Tests for ModelWrapper.from_config classmethod."""

    def test_raises_if_adapter_unavailable(self):
        """When load_dataset_adapter_from_config is None, raises ImportError."""
        with patch("app.core.model_wrapper.load_dataset_adapter_from_config", None):
            with pytest.raises(ImportError, match="config_based_adapter"):
                ModelWrapper.from_config("some/config.json")

    def test_from_config_without_model_path(self):
        """from_config without model_path: does NOT set MODEL_PATH env var."""
        mock_adapter = MagicMock()
        mock_adapter.get_feature_names.return_value = ["f1", "f2"]

        with (
            patch(
                "app.core.model_wrapper.load_dataset_adapter_from_config",
                return_value=mock_adapter,
            ),
            patch.object(ModelWrapper, "__init__", return_value=None) as mock_init,
        ):
            mock_init.return_value = None
            wrapper_instance = MagicMock()
            with patch.object(ModelWrapper, "__new__", return_value=wrapper_instance):
                result = ModelWrapper.from_config("some/config.json")
                assert result is wrapper_instance

    def test_from_config_with_model_path_restores_env(self):
        """from_config with model_path sets MODEL_PATH temporarily, then restores."""
        import os

        mock_adapter = MagicMock()
        original_env = os.environ.get("MODEL_PATH")
        # Ensure MODEL_PATH is not set before the test
        os.environ.pop("MODEL_PATH", None)

        with (
            patch(
                "app.core.model_wrapper.load_dataset_adapter_from_config",
                return_value=mock_adapter,
            ),
            patch.object(ModelWrapper, "__init__", return_value=None),
            patch.object(ModelWrapper, "__new__", return_value=MagicMock()),
        ):
            ModelWrapper.from_config("config.json", model_path="/tmp/model.pkl")
            # After the call, MODEL_PATH should be removed
            assert "MODEL_PATH" not in os.environ

        # Restore
        if original_env is not None:
            os.environ["MODEL_PATH"] = original_env

    def test_from_config_with_model_path_restores_original_path(self):
        """When MODEL_PATH was previously set, from_config restores it."""
        import os

        mock_adapter = MagicMock()
        original_path = "/original/model.pkl"
        os.environ["MODEL_PATH"] = original_path

        with (
            patch(
                "app.core.model_wrapper.load_dataset_adapter_from_config",
                return_value=mock_adapter,
            ),
            patch.object(ModelWrapper, "__init__", return_value=None),
            patch.object(ModelWrapper, "__new__", return_value=MagicMock()),
        ):
            ModelWrapper.from_config("config.json", model_path="/tmp/new_model.pkl")
            assert os.environ.get("MODEL_PATH") == original_path

        # Cleanup
        os.environ["MODEL_PATH"] = original_path


class TestGetModelTypeName:
    """Tests for ModelWrapper.get_model_type_name."""

    def test_no_model_returns_unknown(self):
        wrapper = ModelWrapper.__new__(ModelWrapper)
        wrapper.model = None
        assert wrapper.get_model_type_name() == "Unknown"

    def test_returns_class_name(self):
        wrapper = ModelWrapper.__new__(ModelWrapper)

        class FakeModel:
            pass

        wrapper.model = FakeModel()
        assert wrapper.get_model_type_name() == "FakeModel"

    def test_sklearn_model_name(self):
        from sklearn.ensemble import RandomForestClassifier

        wrapper = ModelWrapper.__new__(ModelWrapper)
        wrapper.model = RandomForestClassifier(n_estimators=2)
        assert wrapper.get_model_type_name() == "RandomForestClassifier"


class TestGetNFeatures:
    """Tests for ModelWrapper.get_n_features."""

    def test_no_model_no_adapter_returns_none(self):
        wrapper = ModelWrapper.__new__(ModelWrapper)
        wrapper.model = None
        wrapper.dataset_adapter = None
        assert wrapper.get_n_features() is None

    def test_returns_n_features_in_from_model(self):
        wrapper = ModelWrapper.__new__(ModelWrapper)
        mock_model = MagicMock()
        mock_model.n_features_in_ = 39
        wrapper.model = mock_model
        assert wrapper.get_n_features() == 39

    def test_fallback_to_dataset_adapter(self):
        wrapper = ModelWrapper.__new__(ModelWrapper)
        wrapper.model = None
        mock_adapter = MagicMock()
        mock_adapter.get_feature_names.return_value = ["a", "b", "c"]
        wrapper.dataset_adapter = mock_adapter
        assert wrapper.get_n_features() == 3

    def test_model_without_n_features_uses_adapter(self):
        wrapper = ModelWrapper.__new__(ModelWrapper)
        mock_model = MagicMock(spec=[])  # spec=[] means no attributes
        wrapper.model = mock_model
        mock_adapter = MagicMock()
        mock_adapter.get_feature_names.return_value = ["x", "y"]
        wrapper.dataset_adapter = mock_adapter
        assert wrapper.get_n_features() == 2


class TestPredictWithConfidenceEnsemble:
    """Tests for the tree-ensemble path in predict_with_confidence."""

    def test_tree_ensemble_path(self):
        """Model with estimators_ triggers the variance-based CI calculation."""
        # Build a minimal RF-like model
        from sklearn.ensemble import RandomForestClassifier

        rf = RandomForestClassifier(n_estimators=3, random_state=42)
        X_train = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        y_train = [0, 1, 0, 1]
        rf.fit(X_train, y_train)

        wrapper = ModelWrapper.__new__(ModelWrapper)
        wrapper.model = rf
        wrapper.model_adapter = MagicMock()
        wrapper.model_adapter.predict_proba.return_value = np.array([0.7])
        wrapper.dataset_adapter = MagicMock()
        wrapper.dataset_adapter.preprocess.return_value = np.array([[0.5, 0.5]])

        result = wrapper.predict_with_confidence({"f1": 0.5, "f2": 0.5})
        assert "prediction" in result
        assert "confidence_interval" in result
        assert "uncertainty" in result
        lower, upper = result["confidence_interval"]
        assert lower <= result["prediction"] <= upper

    def test_heuristic_fallback_path(self):
        """Model without estimators_ triggers the heuristic fallback."""

        class SimpleModel:
            """No estimators_ attribute."""

            def predict_proba(self, X):
                return np.array([[0.3, 0.7]])

        wrapper = ModelWrapper.__new__(ModelWrapper)
        wrapper.model = SimpleModel()
        wrapper.model_adapter = MagicMock()
        wrapper.model_adapter.predict_proba.return_value = np.array([0.7])
        wrapper.dataset_adapter = MagicMock()
        wrapper.dataset_adapter.preprocess.return_value = np.array([[1.0]])

        result = wrapper.predict_with_confidence({"x": 1})
        assert "prediction" in result
        lower, upper = result["confidence_interval"]
        assert lower <= result["prediction"] <= upper

    def test_tree_estimator_1d_output(self):
        """Handle tree estimator returning 1D output (edge case)."""
        wrapper = ModelWrapper.__new__(ModelWrapper)

        # Create mock model with estimators_
        mock_tree = MagicMock()
        mock_tree.predict_proba.return_value = np.array([0.6])  # 1D output

        mock_model = MagicMock()
        mock_model.estimators_ = [mock_tree, mock_tree]
        wrapper.model = mock_model

        wrapper.model_adapter = MagicMock()
        wrapper.model_adapter.predict_proba.return_value = np.array([0.6])
        wrapper.dataset_adapter = MagicMock()
        wrapper.dataset_adapter.preprocess.return_value = np.array([[1.0]])

        result = wrapper.predict_with_confidence({"x": 1})
        assert "prediction" in result
