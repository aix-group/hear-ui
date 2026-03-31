"""Tests to verify prediction consistency across all endpoints."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestPredictVsExplainerConsistency:
    """Verify /predict/simple and /explainer/explain return consistent predictions."""

    def test_predict_vs_explainer_minimal(self, client):
        """Test with minimal data - both should return same prediction."""
        data = {"Alter [J]": 45}

        resp1 = client.post("/api/v1/predict/simple", json=data)
        assert resp1.status_code == 200
        pred1 = resp1.json()["prediction"]

        resp2 = client.post(
            "/api/v1/explainer/explain?method=shap&include_plot=false", json=data
        )
        assert resp2.status_code == 200
        pred2 = resp2.json()["prediction"]

        assert abs(pred1 - pred2) < 0.001, f"Predictions differ: {pred1} vs {pred2}"

    def test_predict_vs_explainer_full(self, client):
        """Test with full data - both should return same prediction."""
        data = {
            "Alter [J]": 65,
            "Geschlecht": "w",
            "Primäre Sprache": "Deutsch",
            "Symptome präoperativ.Tinnitus...": "nein",
            "Behandlung/OP.CI Implantation": "Cochlear",
        }

        resp1 = client.post("/api/v1/predict/simple", json=data)
        assert resp1.status_code == 200
        pred1 = resp1.json()["prediction"]

        resp2 = client.post(
            "/api/v1/explainer/explain?method=shap&include_plot=false", json=data
        )
        assert resp2.status_code == 200
        pred2 = resp2.json()["prediction"]

        assert abs(pred1 - pred2) < 0.001, f"Predictions differ: {pred1} vs {pred2}"

    def test_predict_vs_explainer_male(self, client):
        """Test with male patient - edge case check."""
        data = {
            "Alter [J]": 45,
            "Geschlecht": "m",
            "Symptome präoperativ.Tinnitus...": "ja",
        }

        resp1 = client.post("/api/v1/predict/simple", json=data)
        assert resp1.status_code == 200
        pred1 = resp1.json()["prediction"]

        resp2 = client.post(
            "/api/v1/explainer/explain?method=shap&include_plot=false", json=data
        )
        assert resp2.status_code == 200
        pred2 = resp2.json()["prediction"]

        assert abs(pred1 - pred2) < 0.001, f"Predictions differ: {pred1} vs {pred2}"


class TestPatientExplainerConsistency:
    """Verify /patients/{id}/explainer returns same prediction as /predict/simple."""

    def test_explainer_endpoint_clips_predictions(self, client, db):
        """Patient explainer endpoint should clip predictions to [1%, 99%]."""
        from app.models import Patient

        patient_data = {
            "Alter [J]": 65,
            "Geschlecht": "w",
            "Primäre Sprache": "Deutsch",
            "Symptome präoperativ.Tinnitus...": "nein",
            "Behandlung/OP.CI Implantation": "Cochlear",
        }

        patient = Patient(id=uuid4(), input_features=patient_data)
        db.add(patient)
        db.commit()
        db.refresh(patient)

        resp1 = client.post("/api/v1/predict/simple", json=patient_data)
        assert resp1.status_code == 200
        pred1 = resp1.json()["prediction"]

        resp2 = client.get(f"/api/v1/patients/{patient.id}/explainer")
        assert resp2.status_code == 200
        pred2 = resp2.json()["prediction"]

        assert abs(pred1 - pred2) < 0.001, (
            f"Predictions differ: /predict/simple={pred1:.6f} vs "
            f"/patients/{{id}}/explainer={pred2:.6f}"
        )

        assert 0.01 <= pred1 <= 0.99, f"Prediction {pred1} not clipped correctly"
        assert 0.01 <= pred2 <= 0.99, (
            f"Explainer prediction {pred2} not clipped correctly"
        )

    def test_explainer_endpoint_has_feature_importance(self, client, db):
        """Patient explainer endpoint should return feature importance."""
        from app.models import Patient

        patient_data = {
            "Alter [J]": 45,
            "Geschlecht": "m",
        }

        patient = Patient(id=uuid4(), input_features=patient_data)
        db.add(patient)
        db.commit()
        db.refresh(patient)

        resp = client.get(f"/api/v1/patients/{patient.id}/explainer")
        assert resp.status_code == 200
        data = resp.json()

        assert "prediction" in data
        assert "feature_importance" in data
        assert "shap_values" in data
        assert "base_value" in data

        assert isinstance(data["feature_importance"], dict)
        assert len(data["feature_importance"]) > 0
