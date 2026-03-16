"""Tests targeting uncovered lines in app.api.routes.patients.

Focuses on:
- _extract_birth_year helper (DD.MM.YYYY, YYYY-MM-DD, age fallback)
- _extract_birth_date helper
- _missing_prediction_fields helper
- Additional route edge cases
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Import helpers directly
# ============================================================================

from app.api.routes.patients import (
    _extract_birth_date,
    _extract_birth_year,
)


# ============================================================================
# _extract_birth_year
# ============================================================================


class TestExtractBirthYear:
    def _patient(self, features: dict):
        """Create a minimal patient-like object with input_features."""
        obj = SimpleNamespace(input_features=features)
        return obj

    def test_dd_mm_yyyy_format(self):
        """DD.MM.YYYY format is parsed correctly."""
        p = self._patient({"Geburtsdatum": "15.03.1980"})
        assert _extract_birth_year(p) == 1980

    def test_yyyy_mm_dd_format(self):
        """YYYY-MM-DD format is parsed correctly."""
        p = self._patient({"Geburtsdatum": "1975-07-22"})
        assert _extract_birth_year(p) == 1975

    def test_invalid_dd_mm_yyyy_falls_to_next(self):
        """An invalid DD.MM.YYYY that can't be parsed falls to YYYY-MM-DD path."""
        # Make a "10-char" string with dots but non-numeric year
        p = self._patient({"Geburtsdatum": "01.01.XXXX"})
        # YYYY-MM-DD path also fails, so falls to age
        assert _extract_birth_year(p) is None

    def test_age_fallback(self):
        """When no Geburtsdatum, use Alter [J] to estimate birth year."""
        p = self._patient({"Alter [J]": 45})
        expected = datetime.now(timezone.utc).year - 45
        assert _extract_birth_year(p) == expected

    def test_age_float_fallback(self):
        """Age as float string is also accepted."""
        p = self._patient({"Alter [J]": "50.0"})
        expected = datetime.now(timezone.utc).year - 50
        assert _extract_birth_year(p) == expected

    def test_no_features_returns_none(self):
        """Patient with no input_features returns None."""
        p = SimpleNamespace(input_features=None)
        assert _extract_birth_year(p) is None

    def test_empty_features_returns_none(self):
        """Patient with empty input_features returns None."""
        p = self._patient({})
        assert _extract_birth_year(p) is None

    def test_invalid_age_returns_none(self):
        """Non-numeric age returns None."""
        p = self._patient({"Alter [J]": "not-a-number"})
        assert _extract_birth_year(p) is None

    def test_empty_geburtsdatum_falls_to_age(self):
        """Empty Geburtsdatum string falls through to age."""
        p = self._patient({"Geburtsdatum": "   ", "Alter [J]": 30})
        expected = datetime.now(timezone.utc).year - 30
        assert _extract_birth_year(p) == expected

    def test_geburtsdatum_takes_priority_over_age(self):
        """When Geburtsdatum is present, it takes priority over Alter [J]."""
        p = self._patient({"Geburtsdatum": "15.06.1970", "Alter [J]": 99})
        assert _extract_birth_year(p) == 1970

    def test_no_input_features_attr(self):
        """Object with no input_features attribute falls back gracefully."""

        class NoFeatures:
            pass

        p = NoFeatures()
        assert _extract_birth_year(p) is None


# ============================================================================
# _extract_birth_date
# ============================================================================


class TestExtractBirthDate:
    def _patient(self, features: dict):
        return SimpleNamespace(input_features=features)

    def test_returns_geburtsdatum(self):
        p = self._patient({"Geburtsdatum": "1990-01-15"})
        assert _extract_birth_date(p) == "1990-01-15"

    def test_returns_stripped_value(self):
        p = self._patient({"Geburtsdatum": "  15.03.1980  "})
        assert _extract_birth_date(p) == "15.03.1980"

    def test_returns_none_when_missing(self):
        p = self._patient({})
        assert _extract_birth_date(p) is None

    def test_returns_none_when_empty_string(self):
        p = self._patient({"Geburtsdatum": ""})
        assert _extract_birth_date(p) is None

    def test_returns_none_when_whitespace_only(self):
        p = self._patient({"Geburtsdatum": "   "})
        assert _extract_birth_date(p) is None

    def test_returns_none_when_no_features(self):
        p = SimpleNamespace(input_features=None)
        assert _extract_birth_date(p) is None


# ============================================================================
# Route tests - additional coverage for patients routes
# ============================================================================


class TestPatientsRouteHelpers:
    """Test API routes with targeted edge cases."""

    def test_update_patient_database_error(self, client, db):
        """Test that 500 is returned on DB exception during update."""
        from app import crud
        from app.models import PatientCreate, PatientUpdate

        # Create a patient
        patient_in = PatientCreate(
            input_features={"Alter [J]": 45, "Geschlecht": "m"},
            display_name="Test Update Patient",
        )
        patient = crud.create_patient(session=db, patient_in=patient_in)
        db.commit()
        db.refresh(patient)

        # Patch crud.update_patient to raise an exception
        with patch("app.api.routes.patients.crud.update_patient") as mock_update:
            mock_update.side_effect = Exception("DB connection lost")
            resp = client.put(
                f"/api/v1/patients/{patient.id}",
                json={"display_name": "New Name"},
            )
            assert resp.status_code == 500

    def test_create_patient_sets_display_name(self, client, db):
        """Creating a patient with a display_name stores it correctly."""
        resp = client.post(
            "/api/v1/patients/",
            json={
                "input_features": {
                    "Alter [J]": 55,
                    "Geschlecht": "w",
                    "hl_operated_ear": "Hochgradiger HV",
                },
                "display_name": "Erika Mustermann",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data.get("display_name") == "Erika Mustermann"

    def test_search_patients_returns_results(self, client, db):
        """Search endpoint returns matching patients."""
        from app import crud
        from app.models import PatientCreate

        # Create a patient with a known name
        patient_in = PatientCreate(
            input_features={
                "Alter [J]": 40,
                "Nachname": "Testperson",
                "Vorname": "Anna",
            },
            display_name="Anna Testperson",
        )
        crud.create_patient(session=db, patient_in=patient_in)
        db.commit()

        resp = client.get("/api/v1/patients/search?q=Anna")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_validate_patient_endpoint(self, client, db):
        """Validate endpoint returns fields info for an existing patient."""
        from app import crud
        from app.models import PatientCreate

        patient_in = PatientCreate(
            input_features={
                "Alter [J]": 50,
                "Geschlecht": "m",
                "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
                "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
                "Primäre Sprache": "Deutsch",
            },
        )
        patient = crud.create_patient(session=db, patient_in=patient_in)
        db.commit()
        db.refresh(patient)

        resp = client.get(f"/api/v1/patients/{patient.id}/validate")
        assert resp.status_code == 200
