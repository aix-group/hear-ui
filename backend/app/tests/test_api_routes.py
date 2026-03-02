"""Tests for API routes - comprehensive test coverage."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlmodel import Session

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def sample_patient_data():
    """Sample patient input features."""
    return {
        "Alter [J]": 45,
        "Geschlecht": "w",
        "Primäre Sprache": "Deutsch",
        "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
        "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
        "Symptome präoperativ.Tinnitus...": "ja",
        "Behandlung/OP.CI Implantation": "Cochlear",
    }


@pytest.fixture
def sample_patient(sample_patient_data):
    """Create a sample patient object."""
    from app.models import Patient

    return Patient(
        id=uuid4(), input_features=sample_patient_data, created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_feedback_data():
    """Sample feedback data."""
    return {
        "input_features": {"Alter [J]": 50, "Geschlecht": "m"},
        "prediction": 0.75,
        "explanation": {"age": 0.2},
        "accepted": True,
        "comment": "Good prediction",
    }


# =============================================================================
# Patient Routes Tests
# =============================================================================


class TestPatientRoutes:
    """Tests for /patients endpoints."""

    def test_list_patients_returns_list(self, mock_session, sample_patient):
        """Test that list_patients returns a list of patients."""
        from app.api.routes.patients import list_patients_api

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.list_patients.return_value = [sample_patient]

            result = list_patients_api(
                session=mock_session, limit=100, offset=0, paginated=False
            )

            assert isinstance(result, list)
            assert len(result) == 1
            mock_crud.list_patients.assert_called_once_with(
                session=mock_session, limit=100, offset=0
            )

    def test_list_patients_paginated(self, mock_session, sample_patient):
        """Test that list_patients returns paginated response."""
        from app.api.routes.patients import list_patients_api

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.list_patients.return_value = [sample_patient]
            mock_crud.count_patients.return_value = 1

            result = list_patients_api(
                session=mock_session, limit=100, offset=0, paginated=True
            )

            assert hasattr(result, "items")
            assert hasattr(result, "total")
            assert hasattr(result, "has_more")
            assert result.total == 1
            assert result.has_more is False

    def test_list_patients_empty(self, mock_session):
        """Test that list_patients handles empty list."""
        from app.api.routes.patients import list_patients_api

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.list_patients.return_value = []

            result = list_patients_api(
                session=mock_session, limit=100, offset=0, paginated=False
            )

            assert result == []

    def test_get_patient_found(self, mock_session, sample_patient):
        """Test getting an existing patient."""
        from app.api.routes.patients import get_patient_api

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.get_patient.return_value = sample_patient

            result = get_patient_api(patient_id=sample_patient.id, session=mock_session)

            assert result == sample_patient

    def test_get_patient_not_found(self, mock_session):
        """Test getting a non-existent patient raises 404."""
        from app.api.routes.patients import get_patient_api

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.get_patient.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                get_patient_api(patient_id=uuid4(), session=mock_session)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    def test_validate_patient_ok(self, mock_session, sample_patient):
        """Test validating a patient with all required features."""
        from app.api.routes.patients import validate_patient_api

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.get_patient.return_value = sample_patient

            result = validate_patient_api(
                patient_id=sample_patient.id, session=mock_session
            )

            assert result["ok"] is True
            assert result["missing_features"] == []

    def test_validate_patient_missing_features(self, mock_session):
        """Test validating a patient with missing features."""
        from app.api.routes.patients import validate_patient_api
        from app.models import Patient

        patient = Patient(
            id=uuid4(),
            input_features={},  # Empty features
            created_at=datetime.utcnow(),
        )

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.get_patient.return_value = patient

            result = validate_patient_api(patient_id=patient.id, session=mock_session)

            assert result["ok"] is False
            assert len(result["missing_features"]) > 0

    def test_validate_patient_not_found(self, mock_session):
        """Test validating a non-existent patient."""
        from app.api.routes.patients import validate_patient_api

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.get_patient.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                validate_patient_api(patient_id=uuid4(), session=mock_session)

            assert exc_info.value.status_code == 404

    def test_predict_patient_not_found(self, mock_session):
        """Test prediction for non-existent patient raises 404."""
        from app.api.routes.patients import predict_patient_api

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.get_patient.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                predict_patient_api(patient_id=uuid4(), session=mock_session)

            assert exc_info.value.status_code == 404

    def test_predict_patient_no_features(self, mock_session):
        """Test prediction for patient without features raises 400."""
        from app.api.routes.patients import predict_patient_api
        from app.models import Patient

        patient = Patient(id=uuid4(), input_features={}, created_at=datetime.utcnow())

        with patch("app.api.routes.patients.crud") as mock_crud:
            mock_crud.get_patient.return_value = patient

            with pytest.raises(HTTPException) as exc_info:
                predict_patient_api(patient_id=patient.id, session=mock_session)

            assert exc_info.value.status_code == 400


# =============================================================================
# Feedback Routes Tests
# =============================================================================


class TestFeedbackRoutes:
    """Tests for /feedback endpoints."""

    def test_create_feedback_success(self, mock_session, sample_feedback_data):
        """Test creating feedback successfully."""
        from app.api.routes.feedback import create_feedback
        from app.models import Feedback, FeedbackCreate

        feedback_in = FeedbackCreate(**sample_feedback_data)
        expected_feedback = Feedback(
            id=uuid4(), created_at=datetime.utcnow(), **sample_feedback_data
        )

        with patch("app.api.routes.feedback.crud") as mock_crud:
            mock_crud.create_feedback.return_value = expected_feedback

            result = create_feedback(feedback_in=feedback_in, session=mock_session)

            assert result.prediction == sample_feedback_data["prediction"]
            assert result.accepted == sample_feedback_data["accepted"]

    def test_read_feedback_found(self, mock_session, sample_feedback_data):
        """Test reading existing feedback."""
        from app.api.routes.feedback import read_feedback
        from app.models import Feedback

        feedback_id = uuid4()
        expected_feedback = Feedback(
            id=feedback_id, created_at=datetime.utcnow(), **sample_feedback_data
        )

        with patch("app.api.routes.feedback.crud") as mock_crud:
            mock_crud.get_feedback.return_value = expected_feedback

            result = read_feedback(feedback_id=str(feedback_id), session=mock_session)

            assert result.id == feedback_id

    def test_read_feedback_not_found(self, mock_session):
        """Test reading non-existent feedback raises 404."""
        from app.api.routes.feedback import read_feedback

        with patch("app.api.routes.feedback.crud") as mock_crud:
            mock_crud.get_feedback.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                read_feedback(feedback_id=str(uuid4()), session=mock_session)

            assert exc_info.value.status_code == 404


# =============================================================================
# Predict Routes Tests
# =============================================================================


class TestPredictRoutes:
    """Tests for /predict endpoints."""

    def test_patient_data_model_defaults(self):
        """Test PatientData model has correct defaults (None after removing defaults)."""
        from app.api.routes.predict import PatientData

        patient = PatientData()

        # After removing defaults, fields should be None
        assert patient.alter is None
        assert patient.geschlecht is None
        assert patient.primaere_sprache is None

    def test_patient_data_model_with_values(self):
        """Test PatientData model accepts values."""
        from app.api.routes.predict import PatientData

        patient = PatientData(alter=65, geschlecht="m", primaere_sprache="Englisch")

        assert patient.alter == 65
        assert patient.geschlecht == "m"

    def test_patient_data_model_dump_by_alias(self):
        """Test PatientData model dumps with German column names."""
        from app.api.routes.predict import PatientData

        patient = PatientData(alter=45, geschlecht="w")
        data = patient.model_dump(by_alias=True)

        assert "Alter [J]" in data
        assert "Geschlecht" in data
        assert data["Alter [J]"] == 45
        assert data["Geschlecht"] == "w"


# =============================================================================
# Explainer Routes Tests
# =============================================================================


class TestExplainerRoutes:
    """Tests for /explainer endpoints."""

    def test_shap_visualization_response_structure(self):
        """Test ShapVisualizationResponse has correct structure."""
        from app.api.routes.explainer import ShapVisualizationResponse

        response = ShapVisualizationResponse(
            prediction=0.75,
            features=["age", "gender"],
            values=[45.0, 1.0],
            attributions=[0.1, -0.05],
            base_value=0.5,
            feature_importance={"age": 0.1, "gender": -0.05},
            shap_values=[0.1, -0.05],
        )

        assert response.prediction == 0.75
        assert response.base_value == 0.5
        assert response.plot_base64 is None
        # Standardized aligned-list schema
        assert response.features == ["age", "gender"]
        assert response.values == [45.0, 1.0]
        assert response.attributions == [0.1, -0.05]
        assert len(response.features) == len(response.values) == len(response.attributions)

    def test_shap_visualization_response_lists_aligned(self):
        """All aligned lists must share the same length d."""
        from app.api.routes.explainer import ShapVisualizationResponse

        feat = ["f0", "f1", "f2"]
        vals = [1.0, 2.0, 3.0]
        attrs = [0.3, -0.1, 0.05]

        response = ShapVisualizationResponse(
            prediction=0.8,
            features=feat,
            values=vals,
            attributions=attrs,
            base_value=0.6,
        )

        d = len(feat)
        assert len(response.features) == d
        assert len(response.values) == d
        assert len(response.attributions) == d
        # Verify shap_values defaults empty (not required)
        assert isinstance(response.shap_values, list)

    def test_shap_visualization_response_no_prerendered_images(self):
        """plot_base64 must be None by default (no pre-rendered images in payload)."""
        from app.api.routes.explainer import ShapVisualizationResponse

        response = ShapVisualizationResponse(
            prediction=0.5,
            features=["x"],
            values=[1.0],
            attributions=[0.2],
            base_value=0.3,
        )
        assert response.plot_base64 is None


# =============================================================================
# CRUD Tests
# =============================================================================


class TestCRUD:
    """Tests for CRUD operations."""

    def test_create_feedback(self, mock_session, sample_feedback_data):
        """Test create_feedback CRUD operation."""
        from app import crud
        from app.models import FeedbackCreate

        feedback_in = FeedbackCreate(**sample_feedback_data)

        # Mock session behavior
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        _ = crud.create_feedback(session=mock_session, feedback_in=feedback_in)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_patient(self, mock_session, sample_patient_data):
        """Test create_patient CRUD operation."""
        from app import crud
        from app.models import PatientCreate

        patient_in = PatientCreate(input_features=sample_patient_data)

        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        _ = crud.create_patient(session=mock_session, patient_in=patient_in)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_prediction(self, mock_session):
        """Test create_prediction CRUD operation."""
        from app import crud
        from app.models import PredictionCreate

        prediction_in = PredictionCreate(
            input_features={"Alter [J]": 50}, prediction=0.8, explanation={"age": 0.1}
        )

        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        _ = crud.create_prediction(session=mock_session, prediction_in=prediction_in)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


# =============================================================================
# Model Tests
# =============================================================================


class TestModels:
    """Tests for SQLModel models."""

    def test_patient_model_creation(self, sample_patient_data):
        """Test Patient model can be created."""
        from app.models import Patient

        patient = Patient(input_features=sample_patient_data)

        assert patient.input_features == sample_patient_data
        assert patient.id is not None

    def test_feedback_model_creation(self, sample_feedback_data):
        """Test Feedback model can be created."""
        from app.models import Feedback

        feedback = Feedback(**sample_feedback_data)

        assert feedback.prediction == sample_feedback_data["prediction"]
        assert feedback.accepted == sample_feedback_data["accepted"]
        assert feedback.id is not None

    def test_prediction_model_creation(self):
        """Test Prediction model can be created."""
        from app.models import Prediction

        prediction = Prediction(
            input_features={"Alter [J]": 50}, prediction=0.75, explanation={"age": 0.1}
        )

        assert prediction.prediction == 0.75
        assert prediction.id is not None

    def test_patient_create_schema(self, sample_patient_data):
        """Test PatientCreate schema."""
        from app.models import PatientCreate

        patient_create = PatientCreate(input_features=sample_patient_data)

        assert patient_create.input_features == sample_patient_data

    def test_feedback_create_schema(self, sample_feedback_data):
        """Test FeedbackCreate schema."""
        from app.models import FeedbackCreate

        feedback_create = FeedbackCreate(**sample_feedback_data)

        assert feedback_create.prediction == sample_feedback_data["prediction"]

    def test_prediction_create_schema(self):
        """Test PredictionCreate schema."""
        from app.models import PredictionCreate

        prediction_create = PredictionCreate(
            input_features={"test": "data"}, prediction=0.5, explanation={}
        )

        assert prediction_create.prediction == 0.5


# =============================================================================
# API Dependencies Tests
# =============================================================================


class TestAPIDeps:
    """Tests for API dependencies."""

    def test_get_db_yields_session(self):
        """Test get_db yields a session."""
        from app.api.deps import get_db

        with patch("app.api.deps.engine"):
            with patch("app.api.deps.Session") as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__ = MagicMock(
                    return_value=mock_session
                )
                mock_session_class.return_value.__exit__ = MagicMock(return_value=None)

                gen = get_db()
                session = next(gen)

                assert session is not None
