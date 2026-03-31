"""Integration tests for SHAP endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_predict_endpoint_with_model(client: TestClient):
    """Test predict endpoint returns prediction and explanation."""
    from app.tests.conftest import get_valid_predict_payload

    payload = get_valid_predict_payload()

    response = client.post("/api/v1/predict/", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "prediction" in data
    assert "explanation" in data

    # Verify prediction is numeric
    assert isinstance(data["prediction"], int | float)
    assert 0 <= data["prediction"] <= 1

    # Verification explanation is present (may be empty for basic predict)
    assert isinstance(data["explanation"], dict)


@pytest.mark.integration
def test_predict_endpoint_different_implant_types(client: TestClient):
    """Test predict endpoint handles different implant types."""
    from app.tests.conftest import get_valid_predict_payload

    implant_types = ["Cochlear", "MED-EL", "AB"]

    for implant_type in implant_types:
        payload = get_valid_predict_payload()
        payload["Behandlung/OP.CI Implantation"] = implant_type

        response = client.post("/api/v1/predict/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "explanation" in data


@pytest.mark.integration
def test_predict_endpoint_with_persist(client: TestClient, db):
    """Test predict endpoint can persist predictions."""
    from app.tests.conftest import get_valid_predict_payload

    payload = get_valid_predict_payload()

    response = client.post("/api/v1/predict/?persist=true", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data


@pytest.mark.integration
def test_predict_endpoint_validation(client: TestClient):
    """Test predict endpoint validates input."""
    # Empty payload should now be rejected with 422 due to validation
    payload = {}

    response = client.post("/api/v1/predict/", json=payload)

    # Should fail validation - missing critical fields
    assert response.status_code == 422


@pytest.mark.integration
def test_predict_endpoint_edge_cases(client: TestClient):
    """Test predict endpoint handles edge cases."""
    from app.tests.conftest import get_valid_predict_payload

    # Very young age
    payload1 = get_valid_predict_payload()
    payload1["Alter [J]"] = 18

    response1 = client.post("/api/v1/predict/", json=payload1)
    assert response1.status_code == 200

    # Very old age
    payload2 = get_valid_predict_payload()
    payload2["Alter [J]"] = 90

    response2 = client.post("/api/v1/predict/", json=payload2)
    assert response2.status_code == 200

    # Different gender
    payload3 = get_valid_predict_payload()
    payload3["Geschlecht"] = "w"

    response3 = client.post("/api/v1/predict/", json=payload3)
    assert response3.status_code == 200


@pytest.mark.integration
def test_shap_explain_endpoint(client: TestClient, db):
    """Test SHAP explain endpoint returns detailed explanation."""
    from app import crud
    from app.models import PatientCreate

    # Create patient with test data
    patient_in = PatientCreate(
        input_features={"Alter [J]": 65, "Geschlecht": "w"}, display_name="Test SHAP"
    )
    patient = crud.create_patient(session=db, patient_in=patient_in)
    db.commit()
    db.refresh(patient)

    response = client.get(f"/api/v1/patients/{patient.id}/explainer")

    # Accept either 200 (success) or 503 (model not loaded)
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()

        # Verify response structure
        assert "prediction" in data
        assert "feature_importance" in data
        assert "shap_values" in data
        assert "base_value" in data
        assert "top_features" in data

        # Verify types
        assert isinstance(data["prediction"], int | float)
        assert isinstance(data["feature_importance"], dict)
        assert isinstance(data["shap_values"], list)
        assert isinstance(data["base_value"], int | float)
        assert isinstance(data["top_features"], list)

        # Verify top features structure
        if data["top_features"]:
            assert "feature" in data["top_features"][0]
            assert "importance" in data["top_features"][0]

    elif response.status_code == 503:
        # Model not loaded - expected in some test environments
        data = response.json()
        assert "detail" in data
        assert "Model not loaded" in data["detail"]


@pytest.mark.integration
def test_shap_explain_endpoint_with_plot(client: TestClient, db):
    """Test SHAP explain endpoint (plot generation removed in new implementation)."""
    from app import crud
    from app.models import PatientCreate

    patient_in = PatientCreate(
        input_features={"Alter [J]": 65, "Geschlecht": "w"}, display_name="Test Plot"
    )
    patient = crud.create_patient(session=db, patient_in=patient_in)
    db.commit()
    db.refresh(patient)

    response = client.get(f"/api/v1/patients/{patient.id}/explainer")

    # If model is loaded and SHAP works
    if response.status_code == 200:
        data = response.json()

        # New implementation doesn't generate plots (always None)
        assert data.get("plot_base64") is None


@pytest.mark.integration
def test_model_info_endpoint(client: TestClient):
    """Test model info endpoint returns model status."""
    response = client.get("/api/v1/utils/model-info/")

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "loaded" in data
    assert isinstance(data["loaded"], bool)

    if data["loaded"]:
        # If model is loaded, should have additional info
        assert "model_type" in data or "expected_n_features" in data


@pytest.mark.integration
def test_predict_batch_endpoint(client: TestClient):
    """Test batch prediction endpoint with German column names."""
    # CSV with German column names matching the model's expected format
    csv_content = """Alter [J],Geschlecht,Seiten,Symptome präoperativ.Tinnitus...,Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...
65,w,L,Vorhanden,> 20 y
50,m,R,Kein,5-10 y
70,w,L,Vorhanden,10-20 y
"""

    files = {"file": ("test.csv", csv_content, "text/csv")}

    response = client.post("/api/v1/batch/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "count" in data
    assert "results" in data
    assert data["count"] == 3

    # Verify each result has required fields
    for result in data["results"]:
        assert "prediction" in result
        assert "row" in result
        # Prediction should be a float between 0 and 1
        if result["prediction"] is not None:
            assert 0 <= result["prediction"] <= 1
