"""Utility routes for feature names and model metadata."""

import hashlib
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.feature_config import load_feature_config

router = APIRouter(prefix="/utils", tags=["utils"])

logger = logging.getLogger(__name__)


def _get_model_wrapper(request: Request):
    """Get the canonical model wrapper from app state.

    This ensures all routes use the same model instance,
    preventing prediction inconsistencies.
    """
    wrapper = getattr(request.app.state, "model_wrapper", None)
    if not wrapper:
        raise HTTPException(status_code=503, detail="Model not initialized")
    return wrapper


# Try to load an editable feature config from `app/config/features.yaml`.
# If not present or invalid, fall back to the hard-coded mapping below.
_FEATURE_CONFIG = load_feature_config()


@router.get("/feature-definitions/")
def get_feature_definitions() -> dict[str, Any]:
    """Get comprehensive feature definitions for clinical interpretation.

    Returns detailed information about:
    - Feature types (numeric, categorical, one-hot encoded)
    - Value encodings (e.g., Seiten: L=1, R=2)
    - Clinical meaning of features
    - Expected ranges for numeric features

    This helps clinicians interpret SHAP explanations and feature values.
    """
    from app.core.rf_dataset_adapter import EXPECTED_FEATURES_RF

    return {
        "total_features": len(EXPECTED_FEATURES_RF),
        "feature_types": {
            "numeric": [
                {
                    "name": "PID",
                    "description": "Patient ID (Identifier)",
                    "type": "numeric",
                    "range": "Any positive integer",
                },
                {
                    "name": "Alter [J]",
                    "description": "Alter in Jahren",
                    "type": "numeric",
                    "range": "0-120 Jahre",
                },
                {
                    "name": "Seiten",
                    "description": "Operierte Seite",
                    "type": "numeric_encoded",
                    "encoding": {"1": "L (Links)", "2": "R (Rechts)"},
                },
                {
                    "name": "Symptome präoperativ.Geschmack...",
                    "description": "Geschmacksstörungen präoperativ",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "Symptome präoperativ.Tinnitus...",
                    "description": "Tinnitus präoperativ",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "Symptome präoperativ.Schwindel...",
                    "description": "Schwindel präoperativ",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "Symptome präoperativ.Otorrhoe...",
                    "description": "Otorrhoe präoperativ",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "Symptome präoperativ.Kopfschmerzen...",
                    "description": "Kopfschmerzen präoperativ",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "Diagnose.Höranamnese.Hörminderung operiertes Ohr...",
                    "description": "Grad der Hörminderung am operierten Ohr",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "Diagnose.Höranamnese.Zeitpunkt des Hörverlusts (OP-Ohr)...",
                    "description": "Zeitpunkt des Hörverlusts",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...",
                    "description": "Beginn der Hörminderung",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "Diagnose.Höranamnese.Hochgradige Hörminderung oder Taubheit (OP-Ohr)...",
                    "description": "Hochgradige Hörminderung oder Taubheit",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "Diagnose.Höranamnese.Hörminderung Gegenohr...",
                    "description": "Hörminderung am Gegenohr",
                    "type": "numeric",
                    "range": "Numerischer Wert",
                },
                {
                    "name": "outcome_measurments.pre.measure.",
                    "description": "Präoperative Outcome-Messung",
                    "type": "numeric",
                    "range": "0-100",
                },
                {
                    "name": "abstand",
                    "description": "Abstand zwischen Messungen (in Tagen)",
                    "type": "numeric",
                    "range": "Positive Ganzzahl",
                },
            ],
            "one_hot_encoded": [
                {
                    "category": "Geschlecht",
                    "description": "Geschlecht des Patienten",
                    "features": ["Geschlecht_m", "Geschlecht_w"],
                    "encoding": {
                        "Geschlecht_m": "1.0 = männlich, 0.0 = nicht männlich",
                        "Geschlecht_w": "1.0 = weiblich, 0.0 = nicht weiblich",
                    },
                },
                {
                    "category": "Bildgebung Befunde",
                    "description": "Bildgebungsbefunde präoperativ",
                    "features": [
                        "Bildgebung, präoperativ.Befunde..._Anomalie der Bogengänge, Sonstige",
                        "Bildgebung, präoperativ.Befunde..._Cochleäre Fehlbildung (Sennaroglu), Anomalie der Bogengänge",
                        "Bildgebung, präoperativ.Befunde..._Cochleäre Ossifikation",
                        "Bildgebung, präoperativ.Befunde..._Gehirnpathologie",
                        "Bildgebung, präoperativ.Befunde..._Normalbefund",
                        "Bildgebung, präoperativ.Befunde..._Normalbefund, Sonstige",
                        "Bildgebung, präoperativ.Befunde..._Otosklerose",
                        "Bildgebung, präoperativ.Befunde..._Sonstige",
                        "Bildgebung, präoperativ.Befunde..._Sonstige, Cochleäre Ossifikation",
                        "Bildgebung, präoperativ.Befunde..._Sonstige, Otosklerose",
                        "Bildgebung, präoperativ.Befunde..._nan",
                    ],
                    "encoding": "1.0 = Befund vorhanden, 0.0 = Befund nicht vorhanden",
                },
                {
                    "category": "Objektive Messungen LL",
                    "description": "Objektive Messungen (LL Frequenz)",
                    "features": [
                        "Objektive Messungen.LL..._Keine Reizantwort",
                        "Objektive Messungen.LL..._Nicht erhoben",
                        "Objektive Messungen.LL..._Schwelle",
                    ],
                    "encoding": "1.0 = Kategorie trifft zu, 0.0 = Kategorie trifft nicht zu",
                },
                {
                    "category": "Objektive Messungen 4000 Hz",
                    "description": "Objektive Messungen (4000 Hz Frequenz)",
                    "features": [
                        "Objektive Messungen.4000 Hz..._Keine Reizantwort",
                        "Objektive Messungen.4000 Hz..._Nicht erhoben",
                        "Objektive Messungen.4000 Hz..._Schwelle",
                    ],
                    "encoding": "1.0 = Kategorie trifft zu, 0.0 = Kategorie trifft nicht zu",
                },
                {
                    "category": "Ursache der Hörminderung",
                    "description": "Ursache der Hörminderung",
                    "features": [
                        "Diagnose.Höranamnese.Ursache....Ursache..._Andere",
                        "Diagnose.Höranamnese.Ursache....Ursache..._Hörsturz",
                        "Diagnose.Höranamnese.Ursache....Ursache..._Hörsturz, M. Menière",
                        "Diagnose.Höranamnese.Ursache....Ursache..._Infektiös",
                        "Diagnose.Höranamnese.Ursache....Ursache..._M. Menière",
                        "Diagnose.Höranamnese.Ursache....Ursache..._Other",
                        "Diagnose.Höranamnese.Ursache....Ursache..._Syndromal",
                        "Diagnose.Höranamnese.Ursache....Ursache..._unknown",
                        "Diagnose.Höranamnese.Ursache....Ursache..._nan",
                    ],
                    "encoding": "1.0 = Ursache trifft zu, 0.0 = Ursache trifft nicht zu",
                },
                {
                    "category": "Versorgung Gegenohr",
                    "description": "Versorgung des Gegenohrs",
                    "features": [
                        "Diagnose.Höranamnese.Versorgung Gegenohr..._CI",
                        "Diagnose.Höranamnese.Versorgung Gegenohr..._Hörgerät",
                        "Diagnose.Höranamnese.Versorgung Gegenohr..._Keine Versorgung",
                    ],
                    "encoding": "1.0 = Versorgungsart trifft zu, 0.0 = Versorgungsart trifft nicht zu",
                },
                {
                    "category": "CI Implantation",
                    "description": "Cochlea-Implantat Typ",
                    "features": [
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Advanced Bionics... HiRes Ultra (HiFocus SlimJ)",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Advanced Bionics... HiRes Ultra 3D (HiFocus Mid-Scala)",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Advanced Bionics... HiRes Ultra 3D (HiFocus SlimJ)",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Cochlear... Nucleus Profile CI512 (Contour Advance)",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Cochlear... Nucleus Profile CI522 (Slim Straight)",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Cochlear... Nucleus Profile CI532 (Slim Modiolar)",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Cochlear... Nucleus Profile Plus CI612 (Contour Advance)",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Cochlear... Nucleus Profile Plus CI622 (Slim Straight)",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Cochlear... Nucleus Profile Plus CI632 (Slim Modiolar)",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.MED-EL... Implantattyp, Elektrodentyp",
                        "Behandlung/OP.CI Implantation_Behandlung/OP.CI Implantation.Oticon Medical... Neuro Zti EVO",
                    ],
                    "encoding": "1.0 = Implantat-Typ verwendet, 0.0 = Implantat-Typ nicht verwendet",
                },
                {
                    "category": "Versorgung operiertes Ohr",
                    "description": "Präoperative Versorgung des operierten Ohrs",
                    "features": [
                        "Diagnose.Höranamnese.Versorgung operiertes Ohr..._Hörgerät",
                        "Diagnose.Höranamnese.Versorgung operiertes Ohr..._Keine Versorgung",
                        "Diagnose.Höranamnese.Versorgung operiertes Ohr..._Nicht erhoben",
                        "Diagnose.Höranamnese.Versorgung operiertes Ohr..._Sonstige",
                    ],
                    "encoding": "1.0 = Versorgungsart trifft zu, 0.0 = Versorgungsart trifft nicht zu",
                },
                {
                    "category": "Erwerbsart",
                    "description": "Art des Hörverlusts (Erwerbsart)",
                    "features": [
                        "Diagnose.Höranamnese.Erwerbsart..._Plötzlich",
                        "Diagnose.Höranamnese.Erwerbsart..._Progredient",
                        "Diagnose.Höranamnese.Erwerbsart..._unknown",
                    ],
                    "encoding": "1.0 = Erwerbsart trifft zu, 0.0 = Erwerbsart trifft nicht zu",
                },
                {
                    "category": "Art der Hörstörung",
                    "description": "Typ der Hörstörung",
                    "features": [
                        "Diagnose.Höranamnese.Art der Hörstörung..._Cochleär",
                        "Diagnose.Höranamnese.Art der Hörstörung..._Nicht erhoben",
                        "Diagnose.Höranamnese.Art der Hörstörung..._Schallleitung",
                        "Diagnose.Höranamnese.Art der Hörstörung..._Sonstige",
                    ],
                    "encoding": "1.0 = Hörstörungstyp trifft zu, 0.0 = Hörstörungstyp trifft nicht zu",
                },
            ],
        },
        "interpretation_guide": {
            "one_hot_values": {
                "1.0": "Feature ist aktiv / Kategorie trifft zu",
                "0.0": "Feature ist inaktiv / Kategorie trifft nicht zu",
            },
            "seiten_encoding": {
                "1.0": "L (Linkes Ohr operiert)",
                "2.0": "R (Rechtes Ohr operiert)",
            },
            "numeric_features": "Numerische Features zeigen den tatsächlichen Wert (z.B. Alter in Jahren, Abstand in Tagen)",
            "shap_importance": "Der 'importance'-Wert zeigt, wie stark das Feature zur Vorhersage beiträgt (positiv = erhöht Risiko, negativ = senkt Risiko)",
            "shap_formula": "importance = coefficient × value",
        },
        "all_features": EXPECTED_FEATURES_RF,
    }


@router.get("/health-check/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/model-info/")
def model_info(request: Request):
    """Get model information and metadata.
    Returns information about the loaded model including type,
    feature count, and coefficients for interpretability.
    """
    wrapper = getattr(request.app.state, "model_wrapper", None)
    if wrapper is None:
        return {
            "loaded": False,
            "model_type": "unknown",
            "error": "Model wrapper not initialized",
        }

    info = {
        "loaded": bool(wrapper.is_loaded()),
        "model_type": str(type(getattr(wrapper, "model", None))),
    }

    model_obj = getattr(wrapper, "model", None)
    if model_obj is not None and hasattr(model_obj, "feature_names_in_"):
        info["feature_names_in_"] = list(model_obj.feature_names_in_)

    if model_obj is not None and hasattr(model_obj, "n_features_in_"):
        info["n_features_in_"] = model_obj.n_features_in_

    # Add model file checksum for runtime verification
    # Try both relative and absolute paths
    model_paths = [
        Path("app/models/random_forest_final.pkl"),
        Path("/app/app/models/random_forest_final.pkl"),
        Path(__file__).parent.parent.parent / "models" / "random_forest_final.pkl",
    ]

    for model_path in model_paths:
        if model_path.exists():
            try:
                with open(model_path, "rb") as f:
                    model_bytes = f.read()
                    checksum = hashlib.sha256(model_bytes).hexdigest()
                    info["model_checksum_sha256"] = checksum
                    info["model_file_size_bytes"] = len(model_bytes)
                    info["model_file_path"] = str(model_path)
                    break
            except Exception as e:
                info["model_checksum_error"] = str(e)
                break

    return info


@router.get("/feature-names/")
def get_feature_names() -> dict[str, str]:
    """Get human-readable feature names mapping.

    Returns a dictionary mapping technical feature names (after transformation)
    to human-readable German labels suitable for UI display.
    """

    # If a feature config file exists and was parsed successfully, use it.
    if _FEATURE_CONFIG and _FEATURE_CONFIG.get("mapping"):
        return _FEATURE_CONFIG["mapping"]

    # Fallback: Mapping from technical names to human-readable German labels
    feature_mapping = {
        # Numeric features
        "num__Alter [J]": "Alter (Jahre)",
        # Gender
        "cat__Geschlecht_m": "Geschlecht: Männlich",
        "cat__Geschlecht_w": "Geschlecht: Weiblich",
        # Language
        "cat__Primäre Sprache_Deutsch": "Primärsprache: Deutsch",
        "cat__Primäre Sprache_Englisch": "Primärsprache: Englisch",
        "cat__Primäre Sprache_Arabisch": "Primärsprache: Arabisch",
        "cat__Primäre Sprache_Türkisch": "Primärsprache: Türkisch",
        "cat__Primäre Sprache_Andere": "Primärsprache: Andere",
        # Onset (Beginn der Hörminderung)
        "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._postlingual": "Hörverlust: Nach Spracherwerb (postlingual)",
        "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._praelingual": "Hörverlust: Vor Spracherwerb (prälingual)",
        "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._perilingual": "Hörverlust: Rund um Spracherwerb (perilingual)",
        "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._< 1 y": "Hörverlust: Vor 1 Jahr",
        "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._1-5 y": "Hörverlust: 1-5 Jahre",
        "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._> 20 y": "Hörverlust: Über 20 Jahre",
        "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._Unbekannt": "Hörverlust: Unbekannt",
        # Cause (Ursache)
        "cat__Diagnose.Höranamnese.Ursache....Ursache..._Unbekannt": "Ursache: Unbekannt",
        "cat__Diagnose.Höranamnese.Ursache....Ursache..._Genetisch": "Ursache: Genetisch",
        "cat__Diagnose.Höranamnese.Ursache....Ursache..._Lärm": "Ursache: Lärmbedingt",
        "cat__Diagnose.Höranamnese.Ursache....Ursache..._Meningitis": "Ursache: Meningitis",
        "cat__Diagnose.Höranamnese.Ursache....Ursache..._Syndromal": "Ursache: Syndromal",
        "cat__Diagnose.Höranamnese.Ursache....Ursache..._Posttraumatisch": "Ursache: Posttraumatisch",
        # Tinnitus
        "cat__Symptome präoperativ.Tinnitus..._ja": "Tinnitus: Ja",
        "cat__Symptome präoperativ.Tinnitus..._nein": "Tinnitus: Nein",
        "cat__Symptome präoperativ.Tinnitus..._Vorhanden": "Tinnitus: Vorhanden",
        "cat__Symptome präoperativ.Tinnitus..._Kein": "Tinnitus: Nicht vorhanden",
        # Implant type
        "cat__Behandlung/OP.CI Implantation_Cochlear": "Implantat: Cochlear",
        "cat__Behandlung/OP.CI Implantation_Med-El": "Implantat: Med-El",
        "cat__Behandlung/OP.CI Implantation_Advanced Bionics": "Implantat: Advanced Bionics",
    }

    return feature_mapping


@router.get("/feature-categories/")
def get_feature_categories() -> dict[str, list[str]]:
    """Get features grouped by category for better UI organization.

    Returns features organized by logical categories (Demographics, Diagnosis, etc.)
    """

    # Prefer config categories when available
    if _FEATURE_CONFIG and _FEATURE_CONFIG.get("categories"):
        return _FEATURE_CONFIG["categories"]

    categories = {
        "Demographische Daten": [
            "num__Alter [J]",
            "cat__Geschlecht_m",
            "cat__Geschlecht_w",
            "cat__Primäre Sprache_Deutsch",
            "cat__Primäre Sprache_Englisch",
            "cat__Primäre Sprache_Arabisch",
            "cat__Primäre Sprache_Türkisch",
            "cat__Primäre Sprache_Andere",
        ],
        "Diagnose - Beginn des Hörverlusts": [
            "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._postlingual",
            "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._praelingual",
            "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._perilingual",
            "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._< 1 y",
            "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._1-5 y",
            "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._> 20 y",
            "cat__Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)..._Unbekannt",
        ],
        "Diagnose - Ursache": [
            "cat__Diagnose.Höranamnese.Ursache....Ursache..._Unbekannt",
            "cat__Diagnose.Höranamnese.Ursache....Ursache..._Genetisch",
            "cat__Diagnose.Höranamnese.Ursache....Ursache..._Lärm",
            "cat__Diagnose.Höranamnese.Ursache....Ursache..._Meningitis",
            "cat__Diagnose.Höranamnese.Ursache....Ursache..._Syndromal",
            "cat__Diagnose.Höranamnese.Ursache....Ursache..._Posttraumatisch",
        ],
        "Symptome": [
            "cat__Symptome präoperativ.Tinnitus..._ja",
            "cat__Symptome präoperativ.Tinnitus..._nein",
            "cat__Symptome präoperativ.Tinnitus..._Vorhanden",
            "cat__Symptome präoperativ.Tinnitus..._Kein",
        ],
        "Behandlung": [
            "cat__Behandlung/OP.CI Implantation_Cochlear",
            "cat__Behandlung/OP.CI Implantation_Med-El",
            "cat__Behandlung/OP.CI Implantation_Advanced Bionics",
        ],
    }

    return categories


@router.get("/feature-metadata/")
def get_feature_metadata() -> dict[str, dict[str, Any]]:
    """Return full metadata for features (if config provided).

    This returns a mapping `feature_name -> metadata` as provided in the
    YAML config. If no config is available an empty dict is returned.
    """
    if _FEATURE_CONFIG and _FEATURE_CONFIG.get("metadata"):
        return _FEATURE_CONFIG["metadata"]
    return {}


class PrepareInputRequest(BaseModel):
    """Request model for prepare-input endpoint - accepts any patient data fields."""

    model_config = {"extra": "allow"}  # Allow any additional fields


@router.post("/prepare-input/")
def prepare_input(data: dict[str, Any], request: Request):
    """Debug endpoint: preprocess input JSON and return the 68-D feature vector.

    This endpoint helps validate that the frontend sends correct data and that
    the preprocessing pipeline works as expected. It returns the exact feature
    vector that would be fed to the model.

    Args:
        data: Patient data dict with German column names
        request: FastAPI request object to access app state

    Returns:
        Dict with:
        - feature_vector: List of float values (length depends on model)
        - feature_names: List of feature names (in order)
        - input_data: The original input dict (for reference)
    """
    wrapper = getattr(request.app.state, "model_wrapper", None)
    if wrapper is None:
        raise HTTPException(status_code=503, detail="Model wrapper not initialized")

    if not wrapper.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        import numpy as np

        from app.core.rf_dataset_adapter import EXPECTED_FEATURES_RF

        # Use wrapper's prepare_input to get preprocessed data
        preprocessed = wrapper.prepare_input(data)

        # Convert to flat list
        if hasattr(preprocessed, "values"):
            feature_vector = preprocessed.values.flatten().tolist()
        elif hasattr(preprocessed, "flatten"):
            feature_vector = preprocessed.flatten().tolist()
        else:
            feature_vector = np.array(preprocessed).flatten().tolist()

        return {
            "feature_vector": feature_vector,
            "feature_names": EXPECTED_FEATURES_RF,
            "input_data": data,
            "vector_length": len(feature_vector),
            "expected_length": len(EXPECTED_FEATURES_RF),
        }
    except Exception as e:
        logger.exception("Failed to preprocess input")
        raise HTTPException(
            status_code=400, detail="Failed to preprocess input."
        )
