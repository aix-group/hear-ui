"""Random Forest dataset adapter for Cochlear Implant outcome prediction.

This adapter preprocesses patient data into the 39-feature format expected
by the Random Forest model (random_forest_final.pkl).

IMPORTANT: The exact 39-feature encoding must match the training pipeline.
The feature list and encoding were provided by the model trainer (Khawla Elhadri,
Philipps-Universität Marburg). If updating the model, also update EXPECTED_FEATURES
and the encoding logic below.

Key differences from the old LogisticRegression pipeline:
- 39 features (vs 68 in the LR model)
- Label (ordinal) encoding for most categoricals (vs one-hot in LR)
- No PID feature
- SHAP uses TreeExplainer (fast, exact) instead of LinearExplainer
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from .model_adapter import DatasetAdapter

logger = logging.getLogger(__name__)

# ============================================================================
# FEATURE MAPPING STATUS (Feb 2026):
# [OK] Features 1-32: Mapped to CSV columns (excluding ID, post24, post12)
# [MISSING] Features 33-39: MISSING - Need training notebook from Khawla Elhadri
#
# ANALYSIS: placeholder features have significant importance in the model:
# - _placeholder_39: 0.0400 importance (10th most important!)
# - _placeholder_37: 0.0365 importance
# - _placeholder_36: 0.0216 importance
# These are NOT padding but real engineered features from training.
#
# NOTE: Contact the project's data science team or see the training notebook
# (CI_outcome_prediction.ipynb) for the original feature engineering
# pipeline that creates 39 features from 32 CSV columns.
# ============================================================================

# The 39 feature names in the order expected by the model.
# >>> PLACEHOLDER — MUST be replaced with actual feature list from training code <<<
EXPECTED_FEATURES_RF: list[str] = [
    # --- Confirmed raw columns (label-encoded categoricals + numerics) ---
    "Geschlecht",
    "Alter [J]",
    "Primäre Sprache",
    "Weitere Sprachen",
    "Deutsch Sprachbarriere",
    "non-verbal",
    "Eltern m. Schwerhörigkeit",
    "Geschwister m. SH",
    "Operierte Seiten",
    "Symptome präoperativ.Geschmack...",
    "Symptome präoperativ.Tinnitus...",
    "Symptome präoperativ.Schwindel...",
    "Symptome präoperativ.Otorrhoe...",
    "Symptome präoperativ.Kopfschmerzen...",
    "Bildgebung, präoperativ.Typ...",
    "Bildgebung, präoperativ.Befunde...",
    "Objektive Messungen.OAE (TEOAE/DPOAE)...",
    "Objektive Messungen.LL...",
    "Objektive Messungen.4000 Hz...",
    "Diagnose.Höranamnese.Hörminderung operiertes Ohr...",
    "Diagnose.Höranamnese.Versorgung operiertes Ohr...",
    "Diagnose.Höranamnese.Zeitpunkt des Hörverlusts (OP-Ohr)...",
    "Diagnose.Höranamnese.Erwerbsart...",
    "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...",
    "Diagnose.Höranamnese.Hochgradige Hörminderung oder Taubheit (OP-Ohr)...",
    "Diagnose.Höranamnese.Ursache....Ursache...",
    "Diagnose.Höranamnese.Art der Hörstörung...",
    "Diagnose.Höranamnese.Hörminderung Gegenohr...",
    "Diagnose.Höranamnese.Versorgung Gegenohr...",
    "Behandlung/OP.CI Implantation",
    "outcome_measurments.pre.measure.",
    "abstand",
    # --- Additional columns (7 placeholders — from encoding/feature engineering) ---
    # NOTE: These 7 placeholder features correspond to encoded/engineered
    # columns from the training pipeline. Replace with actual names
    # once the training notebook is available. Current values default to 0.0.
    "_placeholder_33",
    "_placeholder_34",
    "_placeholder_35",
    "_placeholder_36",
    "_placeholder_37",
    "_placeholder_38",
    "_placeholder_39",
]

# Label encoding mappings for categorical columns.
# These MUST match the exact encoding used during training.
# NOTE: Extend with additional mappings from the training notebook
# (LabelEncoder.classes_ for each categorical column).
CATEGORICAL_ENCODINGS: dict[str, dict[str, int]] = {
    "Geschlecht": {"m": 0, "w": 1, "d": 2},
    "Operierte Seiten": {"L": 0, "R": 1},
    # Add more once we have the training notebook...
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float with fallback to default."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _encode_categorical(
    value: Any, mapping: dict[str, int], default: int = -1
) -> float:
    """Encode a categorical value using a label mapping."""
    if value is None:
        return float(default)
    val_str = str(value).strip()
    return float(mapping.get(val_str, default))


class RandomForestDatasetAdapter(DatasetAdapter):
    """Dataset adapter for Random Forest CI outcome prediction.

    Converts raw patient data dictionaries into the 39-feature array
    expected by random_forest_final.pkl.
    """

    def preprocess(self, raw_input: dict) -> np.ndarray:
        """Preprocess CI patient data into 39-feature array for the RF model.

        Args:
            raw_input: Dictionary with patient data (German or English keys)

        Returns:
            Preprocessed feature array (shape: (1, 39))
        """
        features: dict[str, float] = {}

        # --- Numeric features ---
        features["Alter [J]"] = _safe_float(
            raw_input.get(
                "Alter [J]", raw_input.get("alter", raw_input.get("age", 50))
            ),
            50.0,
        )
        features["outcome_measurments.pre.measure."] = _safe_float(
            raw_input.get(
                "outcome_measurments.pre.measure.",
                raw_input.get("pre_measure", 0),
            ),
            0.0,
        )
        features["abstand"] = _safe_float(
            raw_input.get(
                "abstand",
                raw_input.get("days_between", raw_input.get("time_since_surgery", 365)),
            ),
            365.0,
        )

        # --- Categorical features (label-encoded) ---
        gender = str(
            raw_input.get(
                "Geschlecht", raw_input.get("geschlecht", raw_input.get("gender", "w"))
            )
        ).strip()
        features["Geschlecht"] = _encode_categorical(
            gender, CATEGORICAL_ENCODINGS.get("Geschlecht", {}), default=1
        )

        seiten_val = raw_input.get(
            "Operierte Seiten",
            raw_input.get(
                "Seiten",
                raw_input.get("seite", raw_input.get("implant_side", "L")),
            ),
        )
        features["Operierte Seiten"] = _encode_categorical(
            str(seiten_val).strip(),
            CATEGORICAL_ENCODINGS.get("Operierte Seiten", {}),
            default=0,
        )

        # --- Binary symptom features ---
        symptom_fields = {
            "Symptome präoperativ.Geschmack...": ["geschmack", "taste"],
            "Symptome präoperativ.Tinnitus...": ["tinnitus"],
            "Symptome präoperativ.Schwindel...": ["schwindel", "vertigo", "dizziness"],
            "Symptome präoperativ.Otorrhoe...": ["otorrhoe", "ear_discharge"],
            "Symptome präoperativ.Kopfschmerzen...": ["kopfschmerzen", "headache"],
        }
        for feature_name, aliases in symptom_fields.items():
            value = raw_input.get(feature_name, None)
            if value is None:
                for alias in aliases:
                    if alias in raw_input:
                        value = raw_input[alias]
                        break
            if value is not None and isinstance(value, str):
                positive_values = ["ja", "yes", "1", "true", "vorhanden"]
                features[feature_name] = (
                    1.0 if value.lower().strip() in positive_values else 0.0
                )
            else:
                features[feature_name] = 1.0 if value else 0.0

        # --- Other categorical features (label-encoded as integers) ---
        # NOTE: Additional LabelEncoder mappings needed from the training notebook
        # for the following columns. They default to 0.0 for unknown categories.
        other_categoricals = [
            "Primäre Sprache",
            "Weitere Sprachen",
            "Deutsch Sprachbarriere",
            "non-verbal",
            "Eltern m. Schwerhörigkeit",
            "Geschwister m. SH",
            "Bildgebung, präoperativ.Typ...",
            "Bildgebung, präoperativ.Befunde...",
            "Objektive Messungen.OAE (TEOAE/DPOAE)...",
            "Objektive Messungen.LL...",
            "Objektive Messungen.4000 Hz...",
            "Diagnose.Höranamnese.Hörminderung operiertes Ohr...",
            "Diagnose.Höranamnese.Versorgung operiertes Ohr...",
            "Diagnose.Höranamnese.Zeitpunkt des Hörverlusts (OP-Ohr)...",
            "Diagnose.Höranamnese.Erwerbsart...",
            "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...",
            "Diagnose.Höranamnese.Hochgradige Hörminderung oder Taubheit (OP-Ohr)...",
            "Diagnose.Höranamnese.Ursache....Ursache...",
            "Diagnose.Höranamnese.Art der Hörstörung...",
            "Diagnose.Höranamnese.Hörminderung Gegenohr...",
            "Diagnose.Höranamnese.Versorgung Gegenohr...",
            "Behandlung/OP.CI Implantation",
        ]
        for col in other_categoricals:
            if col not in features:
                value = raw_input.get(col, None)
                mapping = CATEGORICAL_ENCODINGS.get(col, {})
                if mapping and value is not None:
                    features[col] = _encode_categorical(value, mapping, default=0)
                else:
                    features[col] = 0.0  # Default until proper encoding is provided

        # --- Placeholder features (7 missing engineered features) ---
        # NOTE: These features have significant model importance but unknown definitions.
        # Setting to 0.0 is a safe default until proper feature engineering is implemented.
        for i in range(33, 40):
            features[f"_placeholder_{i}"] = 0.0

        # Build the final feature vector in the correct order
        vector = [features.get(name, 0.0) for name in EXPECTED_FEATURES_RF]
        return np.array(vector, dtype=np.float64).reshape(1, -1)

    def get_feature_names(self) -> list[str]:
        """Get the 39 RF feature names.

        Returns:
            List of feature names in model input order
        """
        return list(EXPECTED_FEATURES_RF)

    def get_feature_schema(self) -> dict[str, Any]:
        """Get the RF-specific feature schema.

        Returns:
            Dictionary describing features, types, and metadata
        """
        return {
            "dataset_name": "cochlear_implant_outcome_rf",
            "description": "Cochlear implant outcome prediction (Random Forest, 39 features)",
            "n_features": 39,
            "model_type": "RandomForestClassifier",
            "encoding": "label_encoded_categoricals",
            "note": "Feature list and encodings must match the training pipeline from Khawla Elhadri (Uni Marburg)",
            "features": [
                {
                    "name": "Alter [J]",
                    "type": "numeric",
                    "aliases": ["age", "alter"],
                    "default": 50,
                },
                {
                    "name": "Geschlecht",
                    "type": "categorical",
                    "aliases": ["gender"],
                    "values": ["m", "w", "d"],
                },
                {
                    "name": "Behandlung/OP.CI Implantation",
                    "type": "categorical",
                    "aliases": ["implant_type", "ci_type"],
                },
                # ... add remaining features when training notebook is available
            ],
        }

    def validate_input(self, raw_input: dict) -> tuple[bool, str | None]:
        """Validate CI patient data.

        Args:
            raw_input: Dictionary with patient data

        Returns:
            Tuple of (is_valid, error_message)
        """
        age = (
            raw_input.get("Alter [J]") or raw_input.get("age") or raw_input.get("alter")
        )
        if age is not None:
            try:
                age_val = float(age)
                if age_val < 0 or age_val > 120:
                    return False, "Age must be between 0 and 120 years"
            except (ValueError, TypeError):
                return False, "Age must be a valid number"
        return True, None
