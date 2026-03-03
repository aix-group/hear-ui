"""Tests for Explainer API routes."""

from fastapi.testclient import TestClient

from app.core.config import settings


class TestExplainerEndpoint:
    """Tests for GET /patients/{patient_id}/explainer endpoint."""

    def test_explain_returns_valid_response(self, client: TestClient, test_patient):
        """Test that explain endpoint returns valid SHAP response."""
        # Use test_patient fixture which creates a patient in DB
        patient_id = test_patient.id

        resp = client.get(f"{settings.API_V1_STR}/patients/{patient_id}/explainer")

        # Either 200 (success) or 503 (model not loaded)
        assert resp.status_code in [200, 503]

        if resp.status_code == 200:
            data = resp.json()
            # Standardized aligned-list schema (required by task spec)
            assert "features" in data, "Response must contain 'features' list"
            assert "values" in data, "Response must contain 'values' list"
            assert "attributions" in data, "Response must contain 'attributions' list"
            assert "base_value" in data, "Response must contain 'base_value'"
            assert "prediction" in data
            # All aligned lists must have the same length d
            d = len(data["features"])
            assert len(data["values"]) == d, "values list must align with features"
            assert len(data["attributions"]) == d, (
                "attributions list must align with features"
            )
            # No pre-rendered images in payload (optional field)
            assert data.get("plot_base64") is None
            # Backward-compatible fields (still present)
            assert "feature_importance" in data
            assert "shap_values" in data
            assert "top_features" in data

    def test_explain_with_minimal_data(self, client: TestClient, db):
        """Test explain with minimal required fields."""
        from app import crud
        from app.models import PatientCreate

        # Create patient with minimal data
        patient_in = PatientCreate(
            input_features={"Alter [J]": 50, "Geschlecht": "m"},
            display_name="Test Minimal",
        )
        patient = crud.create_patient(session=db, patient_in=patient_in)
        db.commit()
        db.refresh(patient)

        resp = client.get(f"{settings.API_V1_STR}/patients/{patient.id}/explainer")
        # Should accept minimal data (uses defaults)
        assert resp.status_code in [200, 422, 503]

    def test_explain_with_include_plot_false(self, client: TestClient, test_patient):
        """Test explain endpoint (plot is always None in new implementation)."""
        patient_id = test_patient.id

        resp = client.get(f"{settings.API_V1_STR}/patients/{patient_id}/explainer")

        if resp.status_code == 200:
            data = resp.json()
            # New implementation doesn't generate plots
            assert data.get("plot_base64") is None

    def test_explain_top_features_structure(self, client: TestClient, test_patient):
        """Test that top_features has correct structure."""
        patient_id = test_patient.id

        resp = client.get(f"{settings.API_V1_STR}/patients/{patient_id}/explainer")

        if resp.status_code == 200:
            data = resp.json()
            top_features = data.get("top_features", [])

            if top_features:
                for feat in top_features:
                    assert "feature" in feat
                    assert "importance" in feat


class TestExplainerEdgeCases:
    """Edge case tests for explainer."""

    def test_explain_with_extreme_age(self, client: TestClient, db):
        """Test with extreme age values."""
        from app import crud
        from app.models import PatientCreate

        patient_in = PatientCreate(
            input_features={"Alter [J]": 95, "Geschlecht": "w"},
            display_name="Test Extreme Age",
        )
        patient = crud.create_patient(session=db, patient_in=patient_in)
        db.commit()
        db.refresh(patient)

        resp = client.get(f"{settings.API_V1_STR}/patients/{patient.id}/explainer")
        assert resp.status_code in [200, 503]

    def test_explain_with_young_patient(self, client: TestClient, db):
        """Test with young patient."""
        from app import crud
        from app.models import PatientCreate

        patient_in = PatientCreate(
            input_features={"Alter [J]": 5, "Geschlecht": "m"},
            display_name="Test Young",
        )
        patient = crud.create_patient(session=db, patient_in=patient_in)
        db.commit()
        db.refresh(patient)

        resp = client.get(f"{settings.API_V1_STR}/patients/{patient.id}/explainer")
        assert resp.status_code in [200, 503]

    def test_explain_with_all_unknown_values(self, client: TestClient, db):
        """Test with all unknown categorical values."""
        from app import crud
        from app.models import PatientCreate

        patient_in = PatientCreate(
            input_features={
                "Alter [J]": 50,
                "Geschlecht": "d",
                "Primäre Sprache": "Andere",
                "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
            },
            display_name="Test Unknown Values",
        )
        patient = crud.create_patient(session=db, patient_in=patient_in)
        db.commit()
        db.refresh(patient)

        resp = client.get(f"{settings.API_V1_STR}/patients/{patient.id}/explainer")
        assert resp.status_code in [200, 503]


class TestExplainerShapAlias:
    """Tests for the /explainer/shap alias endpoint for backward compatibility."""

    def test_shap_alias_returns_valid_response(self, client: TestClient):
        """Test that /explainer/shap alias works like /explainer/explain."""
        payload = {"age": 50, "gender": "m", "include_plot": False}

        resp = client.post(f"{settings.API_V1_STR}/explainer/shap", json=payload)

        # Should work identically to /explain
        assert resp.status_code in [200, 503]

        if resp.status_code == 200:
            data = resp.json()
            assert "prediction" in data
            assert "feature_importance" in data
            assert "shap_values" in data

    def test_shap_alias_matches_explain_endpoint(self, client: TestClient):
        """Test that /shap and /explain return same results."""
        payload = {"Alter [J]": 45, "Geschlecht": "w", "include_plot": False}

        resp_explain = client.post(
            f"{settings.API_V1_STR}/explainer/explain", json=payload
        )
        resp_shap = client.post(f"{settings.API_V1_STR}/explainer/shap", json=payload)

        assert resp_explain.status_code == resp_shap.status_code

        if resp_explain.status_code == 200:
            from pytest import approx

            data_explain = resp_explain.json()
            data_shap = resp_shap.json()

            # Predictions should be identical (approx for float precision)
            assert data_explain["prediction"] == approx(
                data_shap["prediction"], rel=1e-9
            )
            assert data_explain["base_value"] == approx(
                data_shap["base_value"], rel=1e-9
            )
