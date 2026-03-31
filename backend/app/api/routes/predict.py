"""Prediction routes - FIXED VERSION.

This version correctly handles the full pipeline input format.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import SessionDep
from app.models import Prediction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["prediction"])
limiter = Limiter(key_func=get_remote_address)


class PatientData(BaseModel):
    """Patient data matching the pipeline's expected columns.

    All fields are optional. When a field is omitted, the preprocessor will use
    its own defaults (typically 0 for numeric, empty/unknown for categorical).
    DO NOT add defaults here as they can silently change predictions.
    """

    # Use Field with alias to map Python-friendly names to German column names
    alter: float | None = Field(default=None, alias="Alter [J]")
    geschlecht: str | None = Field(default=None, alias="Geschlecht")
    primaere_sprache: str | None = Field(default=None, alias="Primäre Sprache")
    diagnose_beginn: str | None = Field(
        default=None, alias="Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..."
    )
    diagnose_ursache: str | None = Field(
        default=None, alias="Diagnose.Höranamnese.Ursache....Ursache..."
    )
    symptome_tinnitus: str | None = Field(
        default=None, alias="Symptome präoperativ.Tinnitus..."
    )
    behandlung_ci: str | None = Field(
        default=None, alias="Behandlung/OP.CI Implantation"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
        "json_schema_extra": {
            "example": {
                "Alter [J]": 45,
                "Geschlecht": "w",
                "Primäre Sprache": "Deutsch",
                "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
                "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
                "Symptome präoperativ.Tinnitus...": "ja",
                "Behandlung/OP.CI Implantation": "Cochlear",
            }
        },
    }


def _validate_minimum_input(patient_dict: dict) -> tuple[bool, str | None]:
    """Validate that minimum required fields are present for reliable prediction.

    Medical AI decision support requires sufficient patient data to produce
    clinically meaningful predictions. This function enforces minimum data
    requirements.

    Args:
        patient_dict: Patient data dictionary (German column names)

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if input meets minimum requirements
        - error_message: German error message if validation fails, None otherwise
    """
    # Define critical fields that MUST be present for CI outcome prediction
    CRITICAL_FIELDS = [
        "Alter [J]",  # Age is essential for outcome prediction
        "Geschlecht",  # Gender affects outcomes
        "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...",  # Pre/postlingual crucial
        "Diagnose.Höranamnese.Ursache....Ursache...",  # Etiology affects prognosis
    ]

    # Check for missing critical fields
    missing_critical = []
    for field in CRITICAL_FIELDS:
        if field not in patient_dict or patient_dict[field] is None:
            missing_critical.append(field)

    if missing_critical:
        # Map German column names to user-friendly German labels
        FIELD_LABELS = {
            "Alter [J]": "Alter",
            "Geschlecht": "Geschlecht",
            "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "Beginn der Hörminderung",
            "Diagnose.Höranamnese.Ursache....Ursache...": "Ursache der Hörminderung",
        }
        missing_labels = [FIELD_LABELS.get(f, f) for f in missing_critical]
        return False, (
            f"Unzureichende Patientendaten für eine zuverlässige Vorhersage. "
            f"Folgende Pflichtfelder fehlen: {', '.join(missing_labels)}"
        )

    # Additional check: require minimum number of fields overall
    MIN_FIELDS_TOTAL = 5
    if len(patient_dict) < MIN_FIELDS_TOTAL:
        return False, (
            f"Zu wenige Patientendaten für eine zuverlässige Vorhersage. "
            f"Mindestens {MIN_FIELDS_TOTAL} Felder müssen ausgefüllt sein "
            f"({len(patient_dict)} Felder vorhanden)."
        )

    return True, None


def _calculate_data_completeness(patient_dict: dict, model_wrapper=None) -> dict:
    """Calculate how complete the patient data is.

    Returns:
        Dict with completeness metrics
    """
    # Derive expected feature count from the loaded model when available
    total_features: int = 39  # default fallback
    if model_wrapper is not None:
        try:
            n = model_wrapper.get_n_features()
            if isinstance(n, (int, float)) and n > 0:
                total_features = int(n)
        except Exception:
            pass  # use default fallback

    # Count provided features (non-None, non-empty)
    provided = len([v for v in patient_dict.values() if v is not None and v != ""])

    completeness_percent = (provided / total_features) * 100

    # Classify completeness level
    if completeness_percent >= 80:
        level = "high"
        level_de = "Hoch"
        confidence = "high"
    elif completeness_percent >= 50:
        level = "medium"
        level_de = "Mittel"
        confidence = "medium"
    else:
        level = "low"
        level_de = "Niedrig"
        confidence = "low"

    return {
        "completeness_percent": round(completeness_percent, 1),
        "provided_features": provided,
        "total_features": total_features,
        "level": level,
        "level_de": level_de,
        "confidence": confidence,
    }


@router.post("/")
@limiter.limit("30/minute")
def predict(
    patient: PatientData,
    db: SessionDep,
    request: Request,
    persist: bool = False,
    include_confidence: bool = False,
):
    """Make a prediction for a single patient.

    Args:
        patient: Patient data
        persist: If True, save prediction to database
        include_confidence: If True, include confidence interval and interpretation

    Returns:
        Dict with prediction and optionally confidence interval
    """
    try:
        # Convert to dict with German column names (using aliases)
        # exclude_none=True: don't send None values (let preprocessor use its defaults)
        patient_dict = patient.model_dump(by_alias=True, exclude_none=True)
        logger.debug("Patient dict: %s", patient_dict)

        # Validate minimum input requirements BEFORE accessing model
        is_valid, error_msg = _validate_minimum_input(patient_dict)
        if not is_valid:
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient data: {error_msg} (provided {len(patient_dict)} field(s): {', '.join(patient_dict.keys())})",
            )

        # Use the canonical model wrapper from app state
        model_wrapper = getattr(request.app.state, "model_wrapper", None)
        if model_wrapper:
            logger.debug(
                "Wrapper ID: %s, loaded=%s",
                id(model_wrapper),
                model_wrapper.is_loaded(),
            )

        if not model_wrapper or not model_wrapper.is_loaded():
            raise HTTPException(status_code=503, detail="Model not loaded")

        # Calculate data completeness
        completeness = _calculate_data_completeness(patient_dict, model_wrapper)

        # If caller requested a confidence interval, use predict_with_confidence
        if include_confidence:
            ci_result = model_wrapper.predict_with_confidence(patient_dict)
            prediction = ci_result["prediction"]
        else:
            # Use model_wrapper.predict which handles preprocessing
            # clip=True enforces probability bounds [1%, 99%]
            result = model_wrapper.predict(patient_dict, clip=True)
            logger.debug("Raw result: %s", result)

            # Extract scalar prediction
            try:
                prediction = float(result[0])
            except (TypeError, IndexError):
                prediction = float(result)

        # Persist prediction to DB when requested
        persist_error: str | None = None
        persisted_id: str | None = None

        if persist:
            try:
                pred = Prediction(
                    input_features=patient_dict,
                    prediction=float(prediction),
                    explanation={},
                )
                db.add(pred)
                db.commit()
                db.refresh(pred)
                persisted_id = str(pred.id)
            except Exception as e:
                # Log the error but don't fail the request
                import logging

                logging.getLogger(__name__).warning(
                    f"Failed to persist prediction: {e}"
                )
                persist_error = str(e)
                # Rollback to clean state
                try:
                    db.rollback()
                except Exception:
                    pass

        # Build response
        response = {
            "prediction": float(prediction),
            "explanation": {},  # Basic endpoint doesn't include SHAP
            "data_completeness": completeness,
        }

        # Add confidence interval information if requested
        if include_confidence:
            response["confidence_interval"] = {
                "lower": ci_result["confidence_interval"][0],
                "upper": ci_result["confidence_interval"][1],
            }
            response["uncertainty"] = ci_result["uncertainty"]
            response["confidence_level"] = ci_result["confidence_level"]
            response["interpretation"] = _interpret_prediction(
                prediction, ci_result["uncertainty"]
            )

        # Include persistence info when persist=true was requested
        if persist:
            response["persisted"] = persist_error is None
            if persisted_id:
                response["prediction_id"] = persisted_id
            if persist_error:
                response["persist_error"] = persist_error

        return response

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid input data: {e}")
    except TypeError as e:
        raise HTTPException(status_code=422, detail=f"Incompatible data type: {e}")
    except Exception as e:
        logger.exception("Prediction failed: %s", e)
        raise HTTPException(
            status_code=500, detail="Prediction failed due to an internal error."
        )


def _interpret_prediction(prediction: float, uncertainty: float) -> dict:
    """Provide clinical interpretation of prediction and uncertainty.

    Args:
        prediction: Success probability (0-1)
        uncertainty: Confidence interval width

    Returns:
        Dict with clinical interpretation
    """
    # Classify prediction level
    if prediction >= 0.8:
        level = "very_high"
        level_de = "Sehr hoch"
        description = "Very high probability of successful outcome"
        description_de = "Sehr hohe Wahrscheinlichkeit eines erfolgreichen Ergebnisses"
    elif prediction >= 0.6:
        level = "high"
        level_de = "Hoch"
        description = "High probability of successful outcome"
        description_de = "Hohe Wahrscheinlichkeit eines erfolgreichen Ergebnisses"
    elif prediction >= 0.4:
        level = "moderate"
        level_de = "Mittel"
        description = "Moderate probability of successful outcome"
        description_de = "Mittlere Wahrscheinlichkeit eines erfolgreichen Ergebnisses"
    elif prediction >= 0.2:
        level = "low"
        level_de = "Niedrig"
        description = "Lower probability of successful outcome"
        description_de = "Niedrigere Wahrscheinlichkeit eines erfolgreichen Ergebnisses"
    else:
        level = "very_low"
        level_de = "Sehr niedrig"
        description = "Very low probability of successful outcome"
        description_de = (
            "Sehr niedrige Wahrscheinlichkeit eines erfolgreichen Ergebnisses"
        )

    # Classify uncertainty
    if uncertainty <= 0.10:
        confidence = "high"
        confidence_de = "Hoch"
    elif uncertainty <= 0.20:
        confidence = "moderate"
        confidence_de = "Mittel"
    else:
        confidence = "low"
        confidence_de = "Niedrig"

    return {
        "level": level,
        "level_de": level_de,
        "description": description,
        "description_de": description_de,
        "model_confidence": confidence,
        "model_confidence_de": confidence_de,
        "note": "This prediction should be considered alongside clinical expertise and patient-specific factors.",
        "note_de": "Diese Vorhersage sollte zusammen mit klinischer Expertise und patientenspezifischen Faktoren betrachtet werden.",
    }


def compute_prediction_and_explanation(
    patient: dict[str, Any], model_wrapper
) -> dict[str, Any]:
    """Compute prediction for a patient dict (used by batch endpoint).

    Args:
        patient: Dict with German column names
        model_wrapper: The ModelWrapper instance to use

    Returns:
        Dict with prediction and empty explanation
    """
    # The ModelWrapper handles preprocessing and accepts a raw dict with
    # canonical keys. Prefer using `model_wrapper.predict` so batch upload can
    # provide flexible input (headers normalized before calling this function).
    try:
        # clip=True enforces probability bounds [1%, 99%]
        res = model_wrapper.predict(patient, clip=True)
        # model_wrapper.predict may return array-like; normalize to float
        try:
            prediction = float(res[0])
        except Exception:
            prediction = float(res)

        # Produce SHAP-based feature-importance explanation
        # SHAP provides both positive AND negative contributions (what helps/hurts the prediction)
        explanation: dict = {}
        try:
            from app.core.shap_explainer import ShapExplainer

            model = model_wrapper.model
            if model is not None:
                # Prepare preprocessed sample to get per-feature values
                sample_df = model_wrapper.prepare_input(patient)
                try:
                    sample_vals = (
                        sample_df.values.flatten()
                        if hasattr(sample_df, "values")
                        else sample_df.flatten()
                        if hasattr(sample_df, "flatten")
                        else list(sample_df)
                    )
                except Exception:
                    sample_vals = []

                # Build a raw feature-importance dict using SHAP
                feat_imp: dict[str, float] = {}

                if hasattr(model, "feature_importances_"):
                    # Use SHAP TreeExplainer for tree-based models (Random Forest, etc.)
                    try:
                        feature_names = model_wrapper.get_feature_names()
                        shap_explainer = ShapExplainer(
                            model=model,
                            feature_names=feature_names,
                            use_transformed=True,
                        )

                        # Compute SHAP values
                        explanation_result = shap_explainer.explain(
                            sample_df, return_plot=False
                        )

                        feat_imp = explanation_result.get("feature_importance", {})

                    except Exception as shap_error:
                        logger.warning(
                            "SHAP explanation failed, falling back to feature_importances_: %s",
                            shap_error,
                        )
                        # Fallback to feature_importances_ if SHAP fails
                        importances = model.feature_importances_
                        feature_names = model_wrapper.get_feature_names()
                        for i, fname in enumerate(feature_names):
                            imp = float(importances[i]) if i < len(importances) else 0.0
                            val = float(sample_vals[i]) if i < len(sample_vals) else 0.0
                            feat_imp[fname] = imp * val

                # Map detailed feature names to canonical short keys
                mapping = {
                    "age": ["alter", "age"],
                    "hearing_loss_duration": [
                        "dauer",
                        "hearing",
                        "höranamnese",
                    ],
                    "implant_type": [
                        "implant",
                        "ci implantation",
                        "behandlung",
                    ],
                }
                for short, tokens in mapping.items():
                    total = 0.0
                    for name, val in feat_imp.items():
                        lname = name.lower()
                        if any(tok in lname for tok in tokens):
                            try:
                                total += float(val)
                            except Exception:
                                continue
                    explanation[short] = total
        except Exception:
            # If anything fails during explanation, return empty dict
            explanation = {}

        return {"prediction": prediction, "explanation": explanation}
    except Exception as e:
        raise RuntimeError(f"Prediction failed: {str(e)}")


@router.post("/simple", summary="Get Prediction Only (No Explainer)")
@limiter.limit("30/minute")
def predict_simple(
    patient: PatientData,
    request: Request,
):
    """Make a simple prediction without explanation/SHAP.

    This endpoint is optimized for getting just the prediction value without
    additional SHAP/explainer overhead. It uses the same PatientData model
    as the main /predict endpoint, ensuring consistent feature encoding.

    Args:
        patient: Patient data with German column names

    Returns:
        Dict with prediction value only

    Example:
        POST /predict/simple
        {
            "Alter [J]": 45,
            "Geschlecht": "w",
            "Primäre Sprache": "Deutsch"
        }

        Response:
        {
            "prediction": 0.85
        }
    """
    # Use the canonical model wrapper from app state (same as main predict endpoint)
    model_wrapper = getattr(request.app.state, "model_wrapper", None)

    if not model_wrapper or not model_wrapper.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Convert to dict with German column names (using aliases) - same as main endpoint
        # exclude_none=True: don't send None values (let preprocessor use its defaults)
        patient_dict = patient.model_dump(by_alias=True, exclude_none=True)

        logger.debug("patient_dict: %s", patient_dict)

        # Use model_wrapper.predict which handles preprocessing
        # clip=True enforces probability bounds [1%, 99%]
        result = model_wrapper.predict(patient_dict, clip=True)
        logger.debug("result: %s", result)

        # Extract scalar prediction
        try:
            prediction = float(result[0])
        except (TypeError, IndexError):
            prediction = float(result)

        logger.debug("prediction: %s", prediction)

        return {"prediction": float(prediction)}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Simple prediction failed: %s", e)
        raise HTTPException(
            status_code=500, detail="Prediction failed due to an internal error."
        )
