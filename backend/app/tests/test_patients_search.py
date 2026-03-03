"""Tests for the patient search endpoint."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.models import Patient


def make_patient_with_name(name: str):
    return Patient(
        id=uuid4(), input_features={"Name": name}, created_at=datetime.now(UTC)
    )


def test_search_patients_matches_name():
    """Search should return patient whose `Name` contains query (case-insensitive).

    The search_patients_api first tries DB-side search via crud.search_patients_by_name.
    If that raises an exception, it falls back to Python-side filtering.
    We mock both to test the fallback path.
    """
    from sqlmodel import Session

    from app.api.routes.patients import search_patients_api

    mock_session = MagicMock(spec=Session)

    p1 = make_patient_with_name("Max Mustermann")
    p2 = make_patient_with_name("Anna Beispiel")

    with patch("app.api.routes.patients.crud") as mock_crud:
        # Mock DB-side search to raise so fallback is triggered
        mock_crud.search_patients_by_name.side_effect = Exception(
            "DB search not available"
        )
        mock_crud.list_patients.return_value = [p1, p2]

        res = search_patients_api(q="must", session=mock_session, limit=100)

        assert isinstance(res, list)
        assert {r["id"] for r in res} == {str(p1.id)}
        assert res[0]["name"] == "Max Mustermann"


def test_search_patients_fallback_uses_any_string_value():
    """If no Name key, fallback to first string value inside input_features."""
    from sqlmodel import Session

    from app.api.routes.patients import search_patients_api

    mock_session = MagicMock(spec=Session)

    p = Patient(
        id=uuid4(),
        input_features={"foo": 123, "bar": "Beispiel"},
        created_at=datetime.now(UTC),
    )

    with patch("app.api.routes.patients.crud") as mock_crud:
        # Mock DB-side search to raise so fallback is triggered
        mock_crud.search_patients_by_name.side_effect = Exception(
            "DB search not available"
        )
        mock_crud.list_patients.return_value = [p]

        res = search_patients_api(q="bei", session=mock_session, limit=100)

        assert len(res) == 1
        assert res[0]["name"] == "Beispiel"
