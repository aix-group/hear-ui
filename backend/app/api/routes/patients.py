import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session

from app import crud
from app.api.deps import get_db
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
        # DD.MM.YYYY
        if len(bd) == 10 and bd[2] == "." and bd[5] == ".":
            try:
                return int(bd[6:10])
            except ValueError:
                pass
        # YYYY-MM-DD
        if len(bd) >= 4:
            try:
                return int(bd[:4])
            except ValueError:
                pass
    age = features.get("Alter [J]")
    if age is not None:
        try:
            return datetime.utcnow().year - int(float(age))
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
    session: Session = Depends(get_db),
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
                    f"Mindestfelder für Vorhersage fehlen: {', '.join(missing)}. "
                    "Bitte mindestens Geschlecht, Alter und Hörminderung (operiertes Ohr) angeben."
                ),
            )

        # Create patient in database
        patient = crud.create_patient(session=session, patient_in=patient_in)
        return patient

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create patient")
        raise HTTPException(
            status_code=500, detail=f"Failed to create patient: {str(e)}"
        )


@router.get("/")
def list_patients_api(
    session: Session = Depends(get_db),
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
    q: str = Query(..., min_length=1, description="Search query for patient name"),
    session: Session = Depends(get_db),
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
        for k in ["Nachname", "last_name", "Vorname", "first_name", "Name", "name", "full_name", "fullname"]:
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
    except Exception:
        # If DB-side search is not available or fails (e.g., SQLite/dev),
        # fall back to the conservative Python scanning approach below.
        pass

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
def get_patient_api(patient_id: UUID, session: Session = Depends(get_db)):
    p = crud.get_patient(session=session, patient_id=patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return p


@router.put("/{patient_id}", response_model=Patient)
def update_patient_api(
    patient_id: UUID,
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
    session: Session = Depends(get_db),
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
    except Exception as e:
        logger.exception("Failed to update patient %s", patient_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to update patient: {str(e)}"
        )


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient_api(patient_id: UUID, session: Session = Depends(get_db)):
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
    except Exception as e:
        logger.exception("Failed to delete patient %s", patient_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete patient: {str(e)}"
        )


@router.get("/{patient_id}/predict")
def predict_patient_api(patient_id: UUID, session: Session = Depends(get_db)):
    """Return prediction for a stored patient (uses existing compute helper)."""
    try:
        p = crud.get_patient(session=session, patient_id=patient_id)
        if not p:
            raise HTTPException(status_code=404, detail="Patient not found")

        input_features = p.input_features or {}

        if not input_features:
            raise HTTPException(status_code=400, detail="Patient has no input features")

        # Prefer the app-level model wrapper (app.state) so we rely on the same
        # wrapper instance the rest of the application uses (and its load status).
        try:
            from app.main import app as fastapi_app

            wrapper = getattr(fastapi_app.state, "model_wrapper", None)
        except Exception:
            wrapper = None

        if not wrapper or not wrapper.is_loaded():
            raise HTTPException(status_code=503, detail="Model not loaded")

        try:
            # Use clip=True to enforce probability bounds [1%, 99%]
            model_res = wrapper.predict(input_features, clip=True)
            # extract a scalar prediction from different possible return types
            try:
                prediction = float(model_res[0])
            except (TypeError, IndexError):
                prediction = float(model_res)
            return {"prediction": prediction, "explanation": {}}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Prediction failed for patient %s", patient_id)
            raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in predict_patient_api for %s", patient_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}/explainer")
async def explainer_patient_api(patient_id: UUID, session: Session = Depends(get_db)):
    """Return SHAP explanation for a stored patient by delegating to the SHAP route.

    This constructs a `ShapVisualizationRequest` from the saved input_features
    and calls the existing SHAP handler.
    """
    p = crud.get_patient(session=session, patient_id=patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    input_features = p.input_features or {}

    if not input_features:
        raise HTTPException(status_code=400, detail="Patient has no input features")

    # Use the SAME input_features that the /predict endpoint uses
    # This ensures consistent preprocessing and model predictions
    try:
        from app.main import app as fastapi_app

        wrapper = getattr(fastapi_app.state, "model_wrapper", None)
    except Exception:
        wrapper = None

    if not wrapper or not wrapper.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. SHAP explanations require a loaded model.",
        )

    try:
        import numpy as np

        from app.core.rf_dataset_adapter import EXPECTED_FEATURES_RF

        # Use wrapper.predict() with clip=True to ensure consistent behavior
        # with /predict/simple endpoint (clips to [1%, 99%])
        model_res = wrapper.predict(input_features, clip=True)

        try:
            prediction = float(model_res[0])
        except (TypeError, IndexError):
            prediction = float(model_res)

        # Now prepare preprocessed data separately for feature importance calculation
        preprocessed = wrapper.prepare_input(input_features)

        # Get SHAP-based feature importance (shows both positive AND negative contributions)
        feature_importance = {}
        feature_values = {}
        shap_values = []
        base_value = 0.0

        try:
            from app.core.shap_explainer import ShapExplainer

            model = wrapper.model

            # Get sample values from preprocessed data
            if hasattr(preprocessed, "values"):
                sample_vals = preprocessed.values.flatten()
            elif hasattr(preprocessed, "flatten"):
                sample_vals = preprocessed.flatten()
            else:
                sample_vals = np.array(preprocessed).flatten()

            # Use SHAP TreeExplainer for Random Forest (provides both positive and negative contributions)
            if hasattr(model, "feature_importances_"):
                try:
                    logger.info(
                        "Attempting SHAP TreeExplainer for patient %s", patient_id
                    )
                    # Initialize SHAP explainer
                    shap_explainer = ShapExplainer(
                        model=model,
                        feature_names=EXPECTED_FEATURES_RF,
                        use_transformed=True,
                    )

                    # Compute SHAP values
                    explanation_result = shap_explainer.explain(
                        preprocessed, return_plot=False
                    )

                    feature_importance = explanation_result.get(
                        "feature_importance", {}
                    )
                    shap_values = explanation_result.get("shap_values", [])
                    base_value = explanation_result.get("base_value", 0.0)

                    # Store actual feature values
                    feature_values = {}
                    for i, fname in enumerate(EXPECTED_FEATURES_RF):
                        val = sample_vals[i] if i < len(sample_vals) else 0.0
                        feature_values[fname] = float(val)

                    positive_count = sum(
                        1 for v in feature_importance.values() if v > 0
                    )
                    negative_count = sum(
                        1 for v in feature_importance.values() if v < 0
                    )
                    logger.info(
                        "✅ SHAP SUCCESS for patient %s: %d features, positive=%d, negative=%d",
                        patient_id,
                        len(feature_importance),
                        positive_count,
                        negative_count,
                    )
                    # Log top 10 features for debugging
                    sorted_fi = sorted(
                        feature_importance.items(),
                        key=lambda x: abs(x[1]),
                        reverse=True,
                    )[:10]
                    logger.debug(
                        "SHAP Patient %s — Total features: %d, positive: %d, negative: %d",
                        patient_id,
                        len(feature_importance),
                        positive_count,
                        negative_count,
                    )
                    for fname, val in sorted_fi:
                        sign = "+" if val > 0 else "-" if val < 0 else " "
                        logger.debug("  %s%.4f  %s", sign, abs(val), fname)

                except Exception as shap_error:
                    logger.error(
                        "❌ SHAP explanation failed, falling back to feature_importances_: %s",
                        shap_error,
                        exc_info=True,
                    )
                    # Fallback to feature_importances_ if SHAP fails
                    importances = model.feature_importances_
                    for i, fname in enumerate(EXPECTED_FEATURES_RF):
                        val = sample_vals[i] if i < len(sample_vals) else 0.0
                        importance = (
                            float(importances[i]) if i < len(importances) else 0.0
                        )
                        contribution = importance * val
                        feature_importance[fname] = contribution
                        feature_values[fname] = float(val)
                        shap_values.append(contribution)
            else:
                # For non-tree models, use feature_importances_ fallback
                logger.info(
                    "Model does not have feature_importances_, using empty explanation"
                )
                feature_importance = dict.fromkeys(EXPECTED_FEATURES_RF, 0.0)
                feature_values = dict.fromkeys(EXPECTED_FEATURES_RF, 0.0)
                shap_values = [0.0] * len(EXPECTED_FEATURES_RF)

        except Exception as e:
            logger.warning("Failed to compute feature importance: %s", e)
            # Provide empty but valid response
            feature_importance = dict.fromkeys(EXPECTED_FEATURES_RF, 0.0)
            feature_values = dict.fromkeys(EXPECTED_FEATURES_RF, 0.0)
            shap_values = [0.0] * len(EXPECTED_FEATURES_RF)

        # Get top 5 features by absolute importance
        sorted_feats = sorted(
            feature_importance.items(), key=lambda x: abs(x[1]), reverse=True
        )
        top_features = [
            {"feature": f, "importance": v, "value": feature_values.get(f, 0.0)}
            for f, v in sorted_feats[:5]
        ]

        from app.api.routes.explainer import ShapVisualizationResponse

        # ── Out-of-scope warnings ──────────────────────────────────────────
        from datetime import date as _date
        warnings: list[str] = []
        patient_age: float | None = None
        bd = input_features.get("Geburtsdatum") or ""
        if bd and isinstance(bd, str):
            try:
                bd = bd.strip()
                if len(bd) == 10 and bd[2] == ".":  # DD.MM.YYYY
                    yr = int(bd[6:10])
                elif len(bd) >= 4 and (bd[4] == "-" or len(bd) == 4):  # YYYY-MM-DD or YYYY
                    yr = int(bd[:4])
                else:
                    yr = None
                if yr:
                    patient_age = float(_date.today().year - yr)
            except (ValueError, TypeError):
                pass
        if patient_age is None:
            raw_age = input_features.get("Alter [J]") or input_features.get("age")
            try:
                patient_age = float(raw_age) if raw_age is not None else None
            except (ValueError, TypeError):
                pass
        if patient_age is not None:
            if patient_age < 18:
                warnings.append(
                    f"Patient ist {int(patient_age)} Jahre alt – das Modell wurde ausschließlich "
                    "an Erwachsenen (≥18 Jahre) trainiert. Die Vorhersage ist möglicherweise nicht valide."
                )
            elif patient_age > 90:
                warnings.append(
                    f"Patient ist {int(patient_age)} Jahre alt – der Trainingsbereich des Modells liegt "
                    "typischerweise unter 90 Jahren. Die Vorhersage mit Vorsicht interpretieren."
                )
        # Warn if critical fields are missing
        missing_critical = []
        if not input_features.get("Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..."):
            missing_critical.append("Beginn der Hörminderung")
        if not input_features.get("Diagnose.Höranamnese.Ursache....Ursache..."):
            missing_critical.append("Ursache der Hörminderung")
        if missing_critical:
            missing_str = ", ".join(missing_critical)
            warnings.append(
                f"Fehlende Schlüsselmerkmale: {missing_str}. "
                "Die Vorhersagequalität kann dadurch eingeschränkt sein."
            )
        # ──────────────────────────────────────────────────────────────────

        return ShapVisualizationResponse(
            prediction=prediction,
            feature_importance=feature_importance,
            feature_values=feature_values,
            shap_values=shap_values,
            base_value=base_value,
            plot_base64=None,
            top_features=top_features,
            warnings=warnings,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("SHAP explanation failed for patient %s", patient_id)
        raise HTTPException(status_code=500, detail=f"SHAP explanation failed: {exc}")


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
    session: Session = Depends(get_db),
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

    try:
        from app.main import app as fastapi_app
        wrapper = getattr(fastapi_app.state, "model_wrapper", None)
    except Exception:
        wrapper = None

    if not wrapper or not wrapper.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        model_res = wrapper.predict(merged, clip=True)
        try:
            prediction = float(model_res[0])
        except (TypeError, IndexError):
            prediction = float(model_res)
        return {"prediction": prediction, "overrides": body.overrides}
    except Exception as exc:
        logger.exception("predict-override failed for patient %s", patient_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{patient_id}/validate")
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
    except Exception as e:
        logger.exception("Unexpected error in validate_patient_api for %s", patient_id)
        raise HTTPException(status_code=500, detail=str(e))
