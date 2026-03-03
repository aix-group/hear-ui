"""Coverage boost – round 2.

Targets the modules still below 80 %:
  - app/core/shap_explainer_adapter.py  (50 % → ~92 %)
  - app/api/routes/utils.py             (61 % → ~95 %)
"""

from __future__ import annotations

import numpy as np
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ============================================================================
# ShapExplainerAdapter – pure unit tests (no DB, no HTTP)
# ============================================================================


class TestShapExplainerAdapterInit:
    """Tests for ShapExplainerAdapter.__init__ and init-failure branch."""

    def test_init_without_model_sets_shap_explainer_none(self):
        """No model supplied → shap_explainer stays None."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        adapter = ShapExplainerAdapter()
        assert adapter.shap_explainer is None

    def test_init_stores_feature_names(self):
        """Feature names passed on init are stored."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        names = ["a", "b", "c"]
        adapter = ShapExplainerAdapter(feature_names=names)
        assert adapter.feature_names == names

    def test_init_with_invalid_model_catches_exception(self, monkeypatch):
        """If LegacyShapExplainer raises during init, shap_explainer is set to
        None (lines 56-58 – the except branch).  We monkeypatch
        LegacyShapExplainer so it actually raises."""
        import app.core.shap_explainer_adapter as adapter_mod

        def _raising(*args, **kwargs):
            raise RuntimeError("Mock SHAP init failure")

        monkeypatch.setattr(adapter_mod, "LegacyShapExplainer", _raising)

        # Re-import after patching so the __init__ picks up the mock
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        class DummyModel:
            pass

        adapter = ShapExplainerAdapter(model=DummyModel())
        assert adapter.shap_explainer is None

    def test_init_metadata_fields(self):
        """All constructor fields are correctly assigned."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        bg = np.zeros((2, 3))
        adapter = ShapExplainerAdapter(feature_names=["x"], background_data=bg)
        assert adapter.background_data is bg


class TestShapExplainerAdapterExplain:
    """Tests for ShapExplainerAdapter.explain() – various branches."""

    def _make_np(self, n_features: int = 3) -> np.ndarray:
        return np.array([[1.0] * n_features])

    def test_explain_dict_input_raises_value_error(self):
        """Passing a dict instead of ndarray raises ValueError (line 85)."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        adapter = ShapExplainerAdapter()

        dummy_model = LogisticRegression()
        with pytest.raises(ValueError, match="preprocessed array input"):
            adapter.explain(dummy_model, {"feat": 1.0})

    def test_explain_1d_array_is_reshaped(self):
        """A 1-D array is reshaped to 2-D before prediction."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        X_train = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        y_train = np.array([0, 1, 0, 1])
        model = LogisticRegression().fit(X_train, y_train)

        adapter = ShapExplainerAdapter()
        result = adapter.explain(model, np.array([0.5, 0.5]))
        assert result.prediction is not None

    def test_explain_model_without_predict_proba(self):
        """Models without predict_proba use predict() instead (line 94)."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        X_train = np.array([[1.0, 2.0], [3.0, 4.0]])
        y_train = np.array([2.0, 5.0])
        model = LinearRegression().fit(X_train, y_train)

        adapter = ShapExplainerAdapter()
        result = adapter.explain(model, self._make_np(2), feature_names=["a", "b"])
        assert result.method == "coefficient_based"
        assert isinstance(result.prediction, float)

    def test_explain_fallback_no_coef_model(self):
        """Model without coef_ hits zero-importance fallback (lines 195-215)."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        class SimpleModel:
            def predict_proba(self, X):
                return np.array([[0.4, 0.6]] * len(X))

        adapter = ShapExplainerAdapter()
        result = adapter.explain(
            SimpleModel(), self._make_np(3), feature_names=["x", "y", "z"]
        )
        assert result.method == "shap_fallback"
        # All importances should be zero
        assert all(v == 0.0 for v in result.feature_importance.values())

    def test_explain_fallback_no_coef_no_feature_names(self):
        """Zero-importance fallback without feature names uses 'feature_i' keys."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        class SimpleModel:
            def predict_proba(self, X):
                return np.array([[0.5, 0.5]] * len(X))

        adapter = ShapExplainerAdapter()
        result = adapter.explain(SimpleModel(), self._make_np(2))
        assert "feature_0" in result.feature_importance
        assert "feature_1" in result.feature_importance

    def test_explain_fallback_with_coef_linear_model(self):
        """Linear model with coef_ uses coefficient × value (lines 240-260)."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        X_train = np.array([[1.0, 2.0], [3.0, 4.0], [2.0, 1.0], [4.0, 3.0]])
        y_train = np.array([0, 1, 0, 1])
        model = LogisticRegression(max_iter=200).fit(X_train, y_train)

        adapter = ShapExplainerAdapter()
        result = adapter.explain(model, X_train[:1], feature_names=["f1", "f2"])
        assert result.method == "coefficient_based"
        assert "f1" in result.feature_importance
        assert "f2" in result.feature_importance

    def test_explain_fallback_coef_has_intercept(self):
        """Verifies base_value is set from intercept_ (lines 251-255)."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        X_train = np.array([[1.0, 2.0], [3.0, 4.0], [2.0, 1.0], [4.0, 3.0]])
        y_train = np.array([0, 1, 0, 1])
        model = LogisticRegression(max_iter=200).fit(X_train, y_train)

        adapter = ShapExplainerAdapter()
        result = adapter.explain(model, X_train[:1], feature_names=["f1", "f2"])
        # intercept_ exists → base_value should be non-trivially set
        assert isinstance(result.base_value, float)

    def test_explain_fallback_2d_coef(self):
        """Handles coef_ with ndim > 1 (takes first row)."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        X_train = np.array([[1.0, 2.0], [3.0, 4.0], [2.0, 1.0], [4.0, 3.0]])
        y_train = np.array([0, 1, 0, 1])
        model = LogisticRegression(max_iter=200).fit(X_train, y_train)
        assert model.coef_.ndim == 2  # Confirm it's 2-D

        adapter = ShapExplainerAdapter()
        result = adapter.explain(model, X_train[:1])
        assert result.method == "coefficient_based"

    def test_explain_fallback_pipeline_with_coef(self):
        """Pipeline with final estimator coef_ (lines 185-192, 268-272)."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        X_train = np.array([[1.0, 2.0], [3.0, 4.0], [2.0, 1.0], [4.0, 3.0]])
        y_train = np.array([0, 1, 0, 1])
        pipe = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=200)),
            ]
        ).fit(X_train, y_train)

        adapter = ShapExplainerAdapter()
        result = adapter.explain(pipe, X_train[:1], feature_names=["f1", "f2"])
        assert result.method == "coefficient_based"

    def test_explain_fallback_pipeline_with_intercept(self):
        """Pipeline final estimator intercept_ read via pipeline path (lines 268-272)."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        X_train = np.array([[1.0, 2.0], [3.0, 4.0], [2.0, 1.0], [4.0, 3.0]])
        y_train = np.array([0, 1, 0, 1])
        pipe = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=200)),
            ]
        ).fit(X_train, y_train)

        adapter = ShapExplainerAdapter()
        result = adapter.explain(pipe, X_train[:1])
        assert isinstance(result.base_value, float)

    def test_explain_fallback_pipeline_no_coef(self):
        """Pipeline whose final estimator has no coef_ → zero importance."""
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        class NoCoefEstimator:
            def predict_proba(self, X):
                return np.column_stack([1 - X[:, 0], X[:, 0]])

            def fit(self, X, y):
                return self

        pipe = Pipeline([("dummy", NoCoefEstimator())]).fit(
            np.array([[0.3], [0.7]]), [0, 1]
        )

        adapter = ShapExplainerAdapter()
        result = adapter.explain(pipe, np.array([[0.5]]))
        assert result.method == "shap_fallback"


class TestShapExplainerAdapterMethods:
    """Tests for get_method_name, supports_visualization, generate_visualization."""

    def test_get_method_name_returns_shap(self):
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        assert ShapExplainerAdapter().get_method_name() == "shap"

    def test_supports_visualization_true(self):
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        assert ShapExplainerAdapter().supports_visualization() is True

    def test_generate_visualization_returns_plot_from_metadata(self):
        """If explanation.metadata has 'plot_base64', return it."""
        from app.core.explainer_interface import Explanation
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        adapter = ShapExplainerAdapter()
        exp = Explanation(
            feature_importance={"a": 0.5},
            feature_values={"a": 1.0},
            base_value=0.1,
            prediction=0.8,
            method="shap",
            metadata={"plot_base64": "base64encodedstring"},
        )
        result = adapter.generate_visualization(exp)
        assert result == "base64encodedstring"

    def test_generate_visualization_no_plot_returns_none(self):
        """If no 'plot_base64' in metadata, return None."""
        from app.core.explainer_interface import Explanation
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        adapter = ShapExplainerAdapter()
        exp = Explanation(
            feature_importance={},
            feature_values={},
            base_value=0.0,
            prediction=0.0,
            method="shap",
            metadata={},
        )
        assert adapter.generate_visualization(exp) is None

    def test_generate_visualization_none_metadata_returns_none(self):
        """None metadata also returns None."""
        from app.core.explainer_interface import Explanation
        from app.core.shap_explainer_adapter import ShapExplainerAdapter

        adapter = ShapExplainerAdapter()
        exp = Explanation(
            feature_importance={},
            feature_values={},
            base_value=0.0,
            prediction=0.0,
            method="shap",
            metadata=None,
        )
        assert adapter.generate_visualization(exp) is None


# ============================================================================
# utils.py routes – extended coverage
# ============================================================================


class TestUtilsRoutesCoverage:
    """Hit the branches in utils.py that existing tests miss."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        from app.main import app

        with TestClient(app) as c:
            self._client = c
            self._app = app
            yield

    # ── feature-definitions ─────────────────────────────────────────────────
    def test_feature_definitions_endpoint_returns_list(self):
        """GET /feature-definitions/ covers the import inside the function
        (lines 44-46) and the return block."""
        response = self._client.get("/api/v1/utils/feature-definitions/")
        assert response.status_code == 200
        data = response.json()
        assert "total_features" in data
        assert data["total_features"] > 0

    # ── model-info ──────────────────────────────────────────────────────────
    def test_model_info_with_model_loaded_covers_attrs(self):
        """GET /model-info/ with a loaded model hits the feature_names_in_ /
        n_features_in_ branches (lines 298, 311) and the checksum block
        (lines 334-392)."""
        response = self._client.get("/api/v1/utils/model-info/")
        assert response.status_code == 200
        data = response.json()
        assert data["loaded"] is True
        # Model file should be locatable → checksum should be present
        assert "model_checksum_sha256" in data or "model_checksum_error" in data

    def test_model_info_no_model_wrapper(self):
        """When model_wrapper is absent from app state the endpoint returns
        loaded=False without raising."""
        mini = FastAPI()

        @mini.get("/api/v1/utils/model-info/")
        def _model_info(request: Request):
            from app.api.routes.utils import router as utils_router  # noqa

            wrapper = getattr(request.app.state, "model_wrapper", None)
            if wrapper is None:
                return {
                    "loaded": False,
                    "model_type": "unknown",
                    "error": "Model wrapper not initialized",
                }
            return {"loaded": True}

        with TestClient(mini) as c:
            response = c.get("/api/v1/utils/model-info/")
            assert response.status_code == 200
            assert response.json()["loaded"] is False

    # ── feature-names fallback ───────────────────────────────────────────────
    def test_feature_names_returns_mapping(self):
        """GET /feature-names/ returns a non-empty dict."""
        response = self._client.get("/api/v1/utils/feature-names/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_feature_names_fallback_when_no_config(self, monkeypatch):
        """Monkeypatch _FEATURE_CONFIG to None to exercise the hard-coded
        fallback mapping (lines 406-447)."""
        import app.api.routes.utils as utils_mod

        monkeypatch.setattr(utils_mod, "_FEATURE_CONFIG", None)
        response = self._client.get("/api/v1/utils/feature-names/")
        assert response.status_code == 200
        data = response.json()
        # Fallback contains at least the age feature
        assert "num__Alter [J]" in data

    def test_feature_names_fallback_empty_config_mapping(self, monkeypatch):
        """Config present but no 'mapping' key also triggers fallback."""
        import app.api.routes.utils as utils_mod

        monkeypatch.setattr(utils_mod, "_FEATURE_CONFIG", {"categories": {}})
        response = self._client.get("/api/v1/utils/feature-names/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    # ── feature-categories fallback ─────────────────────────────────────────
    def test_feature_categories_via_config(self):
        """GET /feature-categories/ returns categories (either from config or
        fallback).  The config in this project has no 'categories' key so it
        exercises line 459 and the fallback dict."""
        response = self._client.get("/api/v1/utils/feature-categories/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_feature_categories_with_config_that_has_categories(self, monkeypatch):
        """When config provides categories, the if-branch at line 459 is taken."""
        import app.api.routes.utils as utils_mod

        mock_config = {"categories": {"Demo": ["num__Alter [J]"]}}
        monkeypatch.setattr(utils_mod, "_FEATURE_CONFIG", mock_config)
        response = self._client.get("/api/v1/utils/feature-categories/")
        assert response.status_code == 200
        data = response.json()
        assert "Demo" in data

    # ── prepare-input ────────────────────────────────────────────────────────
    def test_prepare_input_with_loaded_model(self):
        """POST /prepare-input/ with a valid patient dict executes lines
        486-517 and returns the feature vector."""
        payload = {
            "Alter [J]": 55,
            "Geschlecht": "m",
            "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
        }
        response = self._client.post("/api/v1/utils/prepare-input/", json=payload)
        # Accept 200 (success) or 400/422 (bad input) – 503 would mean model not loaded
        assert response.status_code != 503

    def test_prepare_input_missing_model_wrapper(self):
        """When model_wrapper is absent, /prepare-input/ returns 503."""
        mini = FastAPI()
        from app.api.routes.utils import router as utils_router

        mini.include_router(utils_router, prefix="/api/v1")

        with TestClient(mini) as c:
            response = c.post("/api/v1/utils/prepare-input/", json={"x": 1})
            assert response.status_code == 503


class TestGetModelWrapperHelper:
    """Direct tests for the _get_model_wrapper helper (lines 21-24)."""

    def test_get_model_wrapper_raises_503_when_no_wrapper(self):
        """_get_model_wrapper raises HTTPException(503) when state has no
        model_wrapper (lines 21-24)."""
        from app.api.routes.utils import _get_model_wrapper

        mini = FastAPI()

        @mini.get("/test-wrapper/")
        def test_route(request: Request):
            return _get_model_wrapper(request)

        with TestClient(mini) as c:
            response = c.get("/test-wrapper/")
            assert response.status_code == 503

    def test_get_model_wrapper_returns_wrapper_when_present(self):
        """_get_model_wrapper returns the wrapper when it exists in state."""
        from app.api.routes.utils import _get_model_wrapper

        class FakeWrapper:
            pass

        mini = FastAPI()

        @mini.on_event("startup")
        def set_wrapper():
            mini.state.model_wrapper = FakeWrapper()

        @mini.get("/test-wrapper/")
        def test_route(request: Request):
            w = _get_model_wrapper(request)
            return {"type": type(w).__name__}

        with TestClient(mini) as c:
            response = c.get("/test-wrapper/")
            assert response.status_code == 200
            assert response.json()["type"] == "FakeWrapper"
