import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Query, Request, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from app import crud
from app.api.deps import SessionDep
from app.core.explanation_service import (
    compute_patient_warnings,
    compute_shap_explanation,
    get_model_wrapper,
)
from app.models import Patient, PatientCreate, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Minimum fields required to make a meaningful prediction
# Each tuple lists alternative key names (German raw / English normalized / alias)
# ---------------------------------------------------------------------------
_MINIMUM_PREDICTION_GROUPS: list[tuple[str, tuple[str, ...]]] = [
    ("Geschlecht (Gender)", ("Geschlecht", "gender", "geschlecht")),
    ("Alter [J] (Age)", ("Alter [J]", "age", "alter")),
    (
        "Hörminderung operiertes Ohr (Hearing Loss)",
        ("Diagnose.Höranamnese.Hörminderung operiertes Ohr...", "hl_operated_ear"),
    ),
]


def _extract_birth_year(patient) -> int | None:
    """Extract birth year from Geburtsdatum or estimate from age."""
    features = getattr(patient, "input_features", None) or {}
    birth_date = features.get("Geburtsdatum")
    if birth_date and isinstance(birth_date, str) and birth_date.strip():
        bd = birth_date.strip()
        # Try DD.MM.YYYY format
        try:
            parsed = datetime.strptime(bd, "%d.%m.%Y")
            return parsed.year
        except ValueError:
            pass
        # Try YYYY-MM-DD format
        try:
            parsed = datetime.strptime(bd[:10], "%Y-%m-%d")
            return parsed.year
        except ValueError:
            pass
    age = features.get("Alter [J]")
    if age is not None:
        try:
            return datetime.now(UTC).year - int(float(age))
        except (ValueError, TypeError):
            pass
    return None


def _extract_birth_date(patient) -> str | None:
    """Return birth date from Geburtsdatum field as stored string (YYYY-MM-DD or DD.MM.YYYY)."""
    features = getattr(patient, "input_features", None) or {}
    val = features.get("Geburtsdatum")
    if val and isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _missing_prediction_fields(features: dict) -> list[str]:
    """Return human-readable names of minimum groups that are missing/empty."""
    missing = []
    for label, aliases in _MINIMUM_PREDICTION_GROUPS:
        has_value = any(features.get(k) not in (None, "", [], "Keine") for k in aliases)
        if not has_value:
            missing.append(label)
    return missing


class PaginatedPatientsResponse(BaseModel):
    """Paginated response for patient list."""

    items: list[Patient]
    total: int
    limit: int
    offset: int
    has_more: bool


@router.post("/", response_model=Patient, status_code=status.HTTP_201_CREATED)
def create_patient_api(
    session: SessionDep,
    patient_in: PatientCreate = Body(
        ...,
        example={
            "input_features": {
                "Alter [J]": 45,
                "Geschlecht": "w",
                "Primäre Sprache": "Deutsch",
            },
            "display_name": "Muster, Anna",
        },
    ),
):
    """Create a new patient record via JSON (no CSV upload).

    Args:
        patient_in: PatientCreate object with input_features dict and optional display_name
        session: Database session

    Returns:
        Created Patient object with id and created_at

    Example:
        POST /api/v1/patients/
        {
          "input_features": {
            "Alter [J]": 45,
            "Geschlecht": "w",
            "Primäre Sprache": "Deutsch"
          },
          "display_name": "Muster, Anna"
        }
    """
    try:
        # Validate that input_features is provided
        if not patient_in.input_features:
            raise HTTPException(
                status_code=400, detail="input_features is required and cannot be empty"
            )

        # Validate minimum fields required for a prediction
        missing = _missing_prediction_fields(patient_in.input_features)
        if missing:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Missing required prediction fields: {', '.join(missing)}. "
                    "Please provide at least gender, age, and hearing loss (operated ear)."
                ),
            )

        # Silently prevent duplicates (same display_name + Geburtsdatum)
        birth_date = (patient_in.input_features or {}).get("Geburtsdatum")
        existing = crud.find_duplicate_patient(
            session=session,
            display_name=patient_in.display_name,
            birth_date=birth_date,
        )
        if existing:
            return existing

        # Create patient in database
        patient = crud.create_patient(session=session, patient_in=patient_in)
        return patient

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid patient data: {e}")
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="A patient with this data already exists."
        )
    except OperationalError:
        logger.exception("Database error while creating patient")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable.")
    except Exception:
        logger.exception("Failed to create patient")
        raise HTTPException(
            status_code=500, detail="Failed to create patient due to an internal error."
        )


@router.get("/")
def list_patients_api(
    session: SessionDep,
    limit: int = Query(
        default=100, ge=1, le=1000, description="Maximum number of patients to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of patients to skip"),
    paginated: bool = Query(
        default=False, description="Return paginated response with metadata"
    ),
):
    """List patients with optional pagination.

    Args:
        limit: Maximum number of patients (1-1000, default 100)
        offset: Number of patients to skip (default 0)
        paginated: If True, returns {items, total, limit, offset, has_more}
                   If False (default), returns just the list for backward compatibility
    """
    patients = crud.list_patients(session=session, limit=limit, offset=offset)

    if paginated:
        total = crud.count_patients(session=session)
        return PaginatedPatientsResponse(
            items=patients,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(patients)) < total,
        )

    # Backward compatible: return just the list
    return patients


@router.get("/search")
def search_patients_api(
    session: SessionDep,
    q: str = Query(..., min_length=1, description="Search query for patient name"),
    limit: int = Query(
        default=1000, ge=1, le=5000, description="Maximum number of patients to scan"
    ),
    offset: int = Query(
        default=0, ge=0, description="Offset when listing patients to scan"
    ),
):
    """Search patients by name-like fields inside stored `input_features`.

    This performs a simple substring, case-insensitive match against common
    name-like keys found in the `input_features` JSON blob (e.g. `Name`,
    `Vorname`, `Nachname`, `full_name`). The implementation is intentionally
    conservative and runs in Python by fetching a page of patients and
    inspecting their `input_features`. For very large datasets a dedicated
    DB-side JSON query should be implemented.
    """
    # "Nachname" comes first so last-name search takes priority in the fallback path.
    q_lower = q.lower()

    def _build_candidate(input_features: dict) -> str | None:
        """Build a display candidate preferring 'Nachname, Vorname' format."""
        nachname = input_features.get("Nachname") or input_features.get("last_name")
        vorname = input_features.get("Vorname") or input_features.get("first_name")
        if nachname and vorname:
            return f"{nachname}, {vorname}"
        for k in [
            "Nachname",
            "last_name",
            "Vorname",
            "first_name",
            "Name",
            "name",
            "full_name",
            "fullname",
        ]:
            v = input_features.get(k)
            if v:
                return str(v)
        return None

    def _word_start_match(query_lower: str, text: str) -> bool:
        """Match if any name token (first OR last name) starts with query."""
        # Remove commas so 'Müller, Anna' → ['Müller', 'Anna']
        tokens = [tok for tok in text.replace(",", " ").split() if tok]
        return any(tok.lower().startswith(query_lower) for tok in tokens)

    patients = crud.list_patients(session=session, limit=limit, offset=offset)
    # Prefer DB-side search if available (faster for production with Postgres)
    results: list[dict] = []
    try:
        db_results = crud.search_patients_by_name(
            session=session, q=q, limit=limit, offset=offset
        )
        for p in db_results:
            results.append(
                {
                    "id": str(p.id),
                    "name": getattr(p, "display_name", None) or "",
                    "birth_year": _extract_birth_year(p),
                    "birth_date": _extract_birth_date(p),
                }
            )
        return results
    except AttributeError:
        # DB-side search not available (e.g., SQLite/dev) —
        # fall back to the conservative Python scanning approach below.
        logger.debug("DB-side search not available, falling back to Python scan")

    for p in patients:
        if not getattr(p, "input_features", None):
            continue
        input_features = p.input_features or {}
        candidate = _build_candidate(input_features)
        if not candidate:
            # last resort: take the first non-empty string value
            for val in input_features.values():
                if isinstance(val, str) and len(val) > 0:
                    candidate = val
                    break

        if candidate and _word_start_match(q_lower, candidate):
            results.append(
                {
                    "id": str(p.id),
                    "name": candidate,
                    "birth_year": _extract_birth_year(p),
                    "birth_date": _extract_birth_date(p),
                }
            )

    return results


@router.get("/{patient_id}", response_model=Patient)
def get_patient_api(patient_id: UUID, session: SessionDep):
    """Retrieve a single patient by UUID. Returns 404 if not found."""
    p = crud.get_patient(session=session, patient_id=patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return p


@router.put("/{patient_id}", response_model=Patient)
def update_patient_api(
    patient_id: UUID,
    session: SessionDep,
    patient_update: PatientUpdate = Body(
        ...,
        example={
            "input_features": {
                "Alter [J]": 50,
                "Geschlecht": "m",
                "Primäre Sprache": "Deutsch",
            },
            "display_name": "Mustermann, Max",
        },
    ),
):
    """Update an existing patient's data.

    Args:
        patient_id: UUID of the patient to update
        patient_update: PatientUpdate object with fields to update (all optional)
        session: Database session

    Returns:
        Updated Patient object

    Example:
        PUT /api/v1/patients/{patient_id}
        {
          "input_features": {
            "Alter [J]": 50,
            "Geschlecht": "m"
          },
          "display_name": "Mustermann, Max"
        }
    """
    try:
        # Only include fields that were actually provided (not None)
        update_data = patient_update.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        updated_patient = crud.update_patient(
            session=session, patient_id=patient_id, patient_update=update_data
        )

        if not updated_patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        return updated_patient

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid update data: {e}")
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Update conflicts with existing data."
        )
    except OperationalError:
        logger.exception("Database error while updating patient %s", patient_id)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable.")
    except Exception:
        logger.exception("Failed to update patient %s", patient_id)
        raise HTTPException(
            status_code=500, detail="Failed to update patient due to an internal error."
        )


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient_api(patient_id: UUID, session: SessionDep):
    """Delete a patient from the database.

    Args:
        patient_id: UUID of the patient to delete
        session: Database session

    Returns:
        204 No Content on success

    Example:
        DELETE /api/v1/patients/{patient_id}
    """
    try:
        deleted = crud.delete_patient(session=session, patient_id=patient_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Return 204 No Content (FastAPI handles this automatically)
        return None

    except HTTPException:
        raise
    except OperationalError:
        logger.exception("Database error while deleting patient %s", patient_id)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable.")
    except Exception:
        logger.exception("Failed to delete patient %s", patient_id)
        raise HTTPException(
            status_code=500, detail="Failed to delete patient due to an internal error."
        )


@router.get("/{patient_id}/predict")
def predict_patient_api(patient_id: UUID, session: SessionDep):
    """Return prediction for a stored patient (uses existing compute helper)."""
    try:
        p = crud.get_patient(session=session, patient_id=patient_id)
        if not p:
            raise HTTPException(status_code=404, detail="Patient not found")

        input_features = p.input_features or {}

        if not input_features:
            raise HTTPException(status_code=400, detail="Patient has no input features")

        wrapper = get_model_wrapper()
        if not wrapper or not wrapper.is_loaded():
            raise HTTPException(status_code=503, detail="Model not loaded")

        try:
            model_res = wrapper.predict(input_features, clip=True)
            try:
                prediction = float(model_res[0])
            except (TypeError, IndexError):
                prediction = float(model_res)
            return {"prediction": prediction, "explanation": {}}
        except HTTPException:
            raise
        except Exception:
            logger.exception("Prediction failed for patient %s", patient_id)
            raise HTTPException(
                status_code=500, detail="Prediction failed. Please try again later."
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error in predict_patient_api for %s", patient_id)
        raise HTTPException(status_code=500, detail="An internal error occurred.")


@router.get("/{patient_id}/explainer")
async def explainer_patient_api(
    patient_id: UUID, request: Request, session: SessionDep
):
    """Return SHAP explanation for a stored patient.

    Delegates to the shared explanation service to avoid duplicating
    SHAP logic that also exists in the /explainer endpoint.
    """
    from app.api.routes.explainer import ShapVisualizationResponse

    p = crud.get_patient(session=session, patient_id=patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    input_features = p.input_features or {}

    if not input_features:
        raise HTTPException(status_code=400, detail="Patient has no input features")

    wrapper = get_model_wrapper()
    if not wrapper or not wrapper.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. SHAP explanations require a loaded model.",
        )

    try:
        result = compute_shap_explanation(input_features, wrapper)

        accept_lang = request.headers.get("accept-language") or ""
        warnings = compute_patient_warnings(input_features, accept_language=accept_lang)

        return ShapVisualizationResponse(
            prediction=result["prediction"],
            features=result["features"],
            values=result["values"],
            attributions=result["attributions"],
            base_value=result["base_value"],
            plot_base64=None,
            top_features=result["top_features"],
            warnings=warnings,
            feature_importance=result["feature_importance"],
            feature_values=result["feature_values"],
            shap_values=result["shap_values"],
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("SHAP explanation failed for patient %s", patient_id)
        raise HTTPException(
            status_code=500, detail="SHAP explanation failed. Please try again later."
        )


# ---------------------------------------------------------------------------
# What-if / predict-override endpoint
# ---------------------------------------------------------------------------


class _WhatIfRequest(BaseModel):
    """Overrides to apply on top of a patient's stored input_features."""

    overrides: dict[str, Any] = {}


@router.post("/{patient_id}/predict-override")
async def predict_override_api(
    patient_id: UUID,
    body: _WhatIfRequest,
    session: SessionDep,
):
    """Return a new prediction for a patient with some features overridden.

    Merges the patient's stored input_features with the supplied `overrides`
    dict and runs the model. Useful for interactive 'what-if' analysis in the
    frontend without modifying the stored patient record.
    """
    p = crud.get_patient(session=session, patient_id=patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    merged = {**(p.input_features or {}), **body.overrides}

    wrapper = get_model_wrapper()
    if not wrapper or not wrapper.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        model_res = wrapper.predict(merged, clip=True)
        try:
            prediction = float(model_res[0])
        except (TypeError, IndexError):
            prediction = float(model_res)
        return {"prediction": prediction, "overrides": body.overrides}
    except Exception:
        logger.exception("predict-override failed for patient %s", patient_id)
        raise HTTPException(
            status_code=500,
            detail="Prediction override failed. Please try again later.",
        )


@router.get("/{patient_id}/validate")
def validate_patient_api(patient_id: UUID, session: SessionDep):
    """Validate stored patient `input_features` against expected model inputs.

    Returns a JSON object with `ok: bool` and `missing_features: list`.
    """
    try:
        p = crud.get_patient(session=session, patient_id=patient_id)
        if not p:
            raise HTTPException(status_code=404, detail="Patient not found")

        input_features = p.input_features or {}

        # Check for essential features that the preprocessor needs
        has_age = any(k in input_features for k in ["Alter [J]", "alter", "age"])
        has_gender = any(
            k in input_features for k in ["Geschlecht", "geschlecht", "gender"]
        )

        missing = []
        if not has_age:
            missing.append("Alter [J] (age)")
        if not has_gender:
            missing.append("Geschlecht (gender)")

        return {
            "ok": len(missing) == 0,
            "missing_features": missing,
            "features_count": len(input_features),
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error in validate_patient_api for %s", patient_id)
        raise HTTPException(status_code=500, detail="An internal error occurred.")
