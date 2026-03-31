"""Shared explanation computation used by both /explainer and /patients endpoints.

Centralises SHAP/tree-importance logic so that the explainer route and the
per-patient explainer route produce identical results without duplicating code.
"""

from __future__ import annotations

import logging
from datetime import date as _date
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def get_model_wrapper():
    """Return the canonical model wrapper from app state."""
    from app.main import app as fastapi_app

    return getattr(fastapi_app.state, "model_wrapper", None)


def compute_shap_explanation(
    input_features: dict[str, Any],
    wrapper,
    *,
    include_plot: bool = False,
) -> dict[str, Any]:
    """Compute a SHAP-based explanation for *input_features*.

    Returns a dict with keys:
        prediction, features, values, attributions, base_value,
        feature_importance, feature_values, shap_values, top_features,
        plot_base64
    """
    from app.core.rf_dataset_adapter import EXPECTED_FEATURES_RF
    from app.core.shap_explainer import ShapExplainer

    # --- prediction ---
    model_res = wrapper.predict(input_features, clip=True)
    try:
        prediction = float(model_res[0])
    except (TypeError, IndexError):
        prediction = float(model_res)

    # --- preprocessed sample ---
    preprocessed = wrapper.prepare_input(input_features)

    if hasattr(preprocessed, "values"):
        sample_vals = preprocessed.values.flatten()
    elif hasattr(preprocessed, "flatten"):
        sample_vals = preprocessed.flatten()
    else:
        sample_vals = np.array(preprocessed).flatten()

    feature_names: list[str] = list(EXPECTED_FEATURES_RF)
    feature_importance: dict[str, float] = {}
    feature_values: dict[str, float] = {}
    shap_values: list[float] = []
    base_value: float = 0.0

    model = wrapper.model

    try:
        if hasattr(model, "feature_importances_"):
            try:
                shap_explainer = ShapExplainer(
                    model=model,
                    feature_names=feature_names,
                    use_transformed=True,
                )
                explanation_result = shap_explainer.explain(preprocessed, return_plot=False)

                feature_importance = explanation_result.get("feature_importance", {})
                shap_values = explanation_result.get("shap_values", [])
                base_value = explanation_result.get("base_value", 0.0)

                for i, fname in enumerate(feature_names):
                    feature_values[fname] = float(sample_vals[i]) if i < len(sample_vals) else 0.0
            except Exception as shap_error:
                logger.warning("SHAP failed, falling back to feature_importances_: %s", shap_error)
                importances = model.feature_importances_
                for i, fname in enumerate(feature_names):
                    val = float(sample_vals[i]) if i < len(sample_vals) else 0.0
                    imp = float(importances[i]) if i < len(importances) else 0.0
                    feature_importance[fname] = imp * val
                    feature_values[fname] = val
                    shap_values.append(imp * val)
        else:
            feature_importance = dict.fromkeys(feature_names, 0.0)
            feature_values = dict.fromkeys(feature_names, 0.0)
            shap_values = [0.0] * len(feature_names)
    except Exception as e:
        logger.warning("Failed to compute feature importance: %s", e)
        feature_importance = dict.fromkeys(feature_names, 0.0)
        feature_values = dict.fromkeys(feature_names, 0.0)
        shap_values = [0.0] * len(feature_names)

    # --- top features ---
    sorted_feats = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)
    top_features = [
        {"feature": f, "importance": v, "value": feature_values.get(f, 0.0)}
        for f, v in sorted_feats[:5]
    ]

    # --- aligned lists ---
    values_list = [float(feature_values.get(n, 0.0)) for n in feature_names]
    attributions_list = [float(feature_importance.get(n, 0.0)) for n in feature_names]

    return {
        "prediction": prediction,
        "features": feature_names,
        "values": values_list,
        "attributions": attributions_list,
        "base_value": base_value,
        "feature_importance": feature_importance,
        "feature_values": feature_values,
        "shap_values": shap_values,
        "top_features": top_features,
        "plot_base64": None,
    }


# ---------------------------------------------------------------------------
# Warning generation helpers
# ---------------------------------------------------------------------------

def compute_patient_warnings(
    input_features: dict[str, Any],
    *,
    accept_language: str = "",
) -> list[str]:
    """Generate clinical warnings for a patient's input features."""
    warnings: list[str] = []

    # --- Age warnings ---
    patient_age = _extract_patient_age(input_features)
    if patient_age is not None:
        if patient_age < 18:
            warnings.append(
                f"Patient ist {int(patient_age)} Jahre alt – das Modell wurde ausschließlich "
                "an Erwachsenen (≥\u202618 Jahre) trainiert. Die Vorhersage ist möglicherweise nicht valide."
            )
        elif patient_age > 90:
            warnings.append(
                f"Patient ist {int(patient_age)} Jahre alt – der Trainingsbereich des Modells liegt "
                "typischerweise unter 90 Jahren. Die Vorhersage mit Vorsicht interpretieren."
            )

    # --- Missing key fields ---
    _KEY_FIELDS: list[tuple[str, str]] = [
        ("Geschlecht", "Geschlecht"),
        ("Seiten", "Operierte Seite"),
        ("Diagnose.Höranamnese.Hörminderung operiertes Ohr...", "Hörminderung operiertes Ohr"),
    ]
    missing_fields: list[str] = []
    for raw_key, display_name in _KEY_FIELDS:
        val = input_features.get(raw_key)
        if val is None or str(val).strip() in ("", "Keine", "0"):
            missing_fields.append(display_name)

    if missing_fields:
        wants_en = accept_language.lower().startswith("en")
        if wants_en:
            translate_map = {
                "Geschlecht": "Gender",
                "Operierte Seite": "Operated side",
                "Hörminderung operiertes Ohr": "Hearing loss (operated ear)",
            }
            eng_names = [translate_map.get(n, n) for n in missing_fields]
            warnings.append("Missing key fields: " + ", ".join(eng_names) + " — prediction quality may be reduced.")
        else:
            warnings.append("Fehlende Schlüsselfelder: " + ", ".join(missing_fields) + " – die Vorhersagequalität kann eingeschränkt sein.")

    return warnings


def _extract_patient_age(input_features: dict[str, Any]) -> float | None:
    """Best-effort extraction of patient age from input features."""
    bd = input_features.get("Geburtsdatum") or ""
    if bd and isinstance(bd, str):
        try:
            bd = bd.strip()
            if len(bd) == 10 and bd[2] == ".":
                yr = int(bd[6:10])
            elif len(bd) >= 4 and (bd[4] == "-" or len(bd) == 4):
                yr = int(bd[:4])
            else:
                yr = None
            if yr:
                return float(_date.today().year - yr)
        except (ValueError, TypeError):
            pass

    raw_age = input_features.get("Alter [J]")
    if raw_age is None:
        raw_age = input_features.get("age")
    try:
        if raw_age is not None:
            candidate = float(raw_age)
            if candidate >= 0:
                return candidate
    except (ValueError, TypeError):
        pass
    return None
