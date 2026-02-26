from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from app.models.model_card.model_card import load_model_card

router = APIRouter(prefix="/model-card", tags=["Model Card"])

# ---------------------------------------------------------------------------
# Feature name translations: German (raw DB/model names) → English display
# ---------------------------------------------------------------------------
FEATURE_TRANSLATIONS_DE_EN: dict[str, str] = {
    # Demographics
    "Geschlecht": "Gender",
    "Alter [J]": "Age (years)",
    "Operierte Seiten": "Operated Side (L/R)",
    # Language & Communication
    "Primäre Sprache": "Primary Language",
    "Weitere Sprachen": "Additional Languages",
    "Deutsch Sprachbarriere": "German Language Barrier",
    "non-verbal": "Non-verbal",
    # Family history
    "Eltern m. Schwerhörigkeit": "Parents with Hearing Loss",
    "Geschwister m. SH": "Siblings with Hearing Loss",
    # Preoperative symptoms
    "Symptome präoperativ.Geschmack...": "Preop Symptom: Taste Disturbance",
    "Symptome präoperativ.Tinnitus...": "Preop Symptom: Tinnitus",
    "Symptome präoperativ.Schwindel...": "Preop Symptom: Vertigo / Dizziness",
    "Symptome präoperativ.Otorrhoe...": "Preop Symptom: Otorrhea",
    "Symptome präoperativ.Kopfschmerzen...": "Preop Symptom: Headaches",
    # Imaging & Diagnostics
    "Bildgebung, präoperativ.Typ...": "Imaging: Scan Type",
    "Bildgebung, präoperativ.Befunde...": "Imaging: Findings",
    # Objective measurements
    "Objektive Messungen.OAE (TEOAE/DPOAE)...": "OAE",
    "Objektive Messungen.LL...": "LL",
    "Objektive Messungen.4000 Hz...": "4000 Hz",
    # Hearing history & diagnosis
    "Diagnose.Höranamnese.Hörminderung operiertes Ohr...": "Hearing Loss (Operated Ear)",
    "Diagnose.Höranamnese.Versorgung operiertes Ohr...": "Hearing Aid / Device – Operated Ear",
    "Diagnose.Höranamnese.Zeitpunkt des Hörverlusts (OP-Ohr)...": "Onset Time of Hearing Loss (Operated Ear)",
    "Diagnose.Höranamnese.Erwerbsart...": "Hearing Loss Acquisition Type",
    "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "Onset of Hearing Loss (Operated Ear)",
    "Diagnose.Höranamnese.Hochgradige Hörminderung oder Taubheit (OP-Ohr)...": "Severe Hearing Loss or Deafness (Operated Ear)",
    "Diagnose.Höranamnese.Ursache....Ursache...": "Etiology / Cause of Hearing Loss",
    "Diagnose.Höranamnese.Art der Hörstörung...": "Type of Hearing Disorder",
    "Diagnose.Höranamnese.Hörminderung Gegenohr...": "Hearing Loss (Contralateral)",
    "Diagnose.Höranamnese.Versorgung Gegenohr...": "Hearing Device (Contralateral)",
    # Treatment & CI implantation
    "Behandlung/OP.CI Implantation": "CI Implantation / Treatment",
    # Outcome
    "outcome_measurments.pre.measure.": "Outcome: Preoperative",
    "abstand": "Outcome: Time Interval (Days)",
}

# ---------------------------------------------------------------------------
# Clean German display names for the model card feature list
# ---------------------------------------------------------------------------
FEATURE_DISPLAY_NAMES_DE: dict[str, str] = {
    "Geschlecht": "Geschlecht",
    "Alter [J]": "Alter [J]",
    "Operierte Seiten": "Operierte Seite (L/R)",
    "Primäre Sprache": "Primäre Sprache",
    "Weitere Sprachen": "Weitere Sprachen",
    "Deutsch Sprachbarriere": "Deutsch Sprachbarriere",
    "non-verbal": "Non-verbal",
    "Eltern m. Schwerhörigkeit": "Eltern m. Schwerhörigkeit",
    "Geschwister m. SH": "Geschwister m. Schwerhörigkeit",
    "Symptome präoperativ.Geschmack...": "Geschmacksstörung (präop.)",
    "Symptome präoperativ.Tinnitus...": "Tinnitus (präop.)",
    "Symptome präoperativ.Schwindel...": "Schwindel (präop.)",
    "Symptome präoperativ.Otorrhoe...": "Otorrhoe (präop.)",
    "Symptome präoperativ.Kopfschmerzen...": "Kopfschmerzen (präop.)",
    "Bildgebung, präoperativ.Typ...": "Bildgebung: Typ",
    "Bildgebung, präoperativ.Befunde...": "Bildgebung: Befund",
    "Objektive Messungen.OAE (TEOAE/DPOAE)...": "OAE",
    "Objektive Messungen.LL...": "LL",
    "Objektive Messungen.4000 Hz...": "4000 Hz",
    "Diagnose.Höranamnese.Hörminderung operiertes Ohr...": "Hörminderung (operiertes Ohr)",
    "Diagnose.Höranamnese.Versorgung operiertes Ohr...": "Versorgung operiertes Ohr",
    "Diagnose.Höranamnese.Zeitpunkt des Hörverlusts (OP-Ohr)...": "Zeitpunkt des Hörverlusts (OP-Ohr)",
    "Diagnose.Höranamnese.Erwerbsart...": "Erwerbsart",
    "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "Beginn der Hörminderung (OP-Ohr)",
    "Diagnose.Höranamnese.Hochgradige Hörminderung oder Taubheit (OP-Ohr)...": "Hochgradige Hörminderung / Taubheit (OP-Ohr)",
    "Diagnose.Höranamnese.Ursache....Ursache...": "Diagnose.Höranamnese.Ursache",
    "Diagnose.Höranamnese.Art der Hörstörung...": "Art der Hörstörung",
    "Diagnose.Höranamnese.Hörminderung Gegenohr...": "Hörminderung (Gegenohr)",
    "Diagnose.Höranamnese.Versorgung Gegenohr...": "Versorgung (Gegenohr)",
    "Behandlung/OP.CI Implantation": "Behandlung/OP.CI Implantation",
    "outcome_measurments.pre.measure.": "Outcome.Präoperativ",
    "abstand": "Outcome.Abstand (Tage)",
}


def _render_model_card_markdown_de() -> str:
    """Build a German Markdown string from the loaded ModelCard."""
    card = load_model_card()

    # Build metrics section only if metrics are available
    metrics_section = ""
    if card.metrics and any(
        [
            card.metrics.accuracy,
            card.metrics.precision,
            card.metrics.recall,
            card.metrics.f1_score,
            card.metrics.roc_auc,
        ]
    ):
        dataset_size = (
            card.metadata.get("dataset_size")
            if getattr(card, "metadata", None)
            else None
        )
        ds_label = f"N={dataset_size}" if dataset_size else "N=?"
        metrics_section = "\n## 📊 Leistung / Bewertung\n\n"
        # Render as a vertical numbered list: 1) Train/Test set, 2) Metrics combined
        metrics_section += f'1. <strong class="text-primary">Trainings-/Test-Set:</strong> 80/20 Split ({ds_label})\n'

        parts: list[str] = []
        if card.metrics.accuracy is not None:
            parts.append(
                f'<strong class="text-primary">Genauigkeit:</strong> {card.metrics.accuracy:.2%}'
            )
        if card.metrics.roc_auc is not None:
            parts.append(f"**ROC-AUC:** {card.metrics.roc_auc:.2f}")
        if card.metrics.recall is not None:
            parts.append(f"**Sensitivität (Recall):** {card.metrics.recall:.2%}")
        if card.metrics.precision is not None:
            parts.append(f"**Spezifität (Precision):** {card.metrics.precision:.2%}")
        if card.metrics.f1_score is not None:
            parts.append(
                f'<strong class="text-primary">F1-Score:</strong> {card.metrics.f1_score:.2f}'
            )

        metrics_combined = " | ".join(parts) if parts else "Metriken nicht verfügbar"
        metrics_section += f"2. {metrics_combined}\n\n"
        metrics_section += "\n> **Hinweis:** Zahlen dienen zur Orientierung, nicht zur alleinigen Entscheidungsfindung.\n"

    # Group features
    feature_groups = _group_features(card.features)

    features_section = "\n## 📋 Merkmale\n\n"
    features_section += f"**Gesamt: {len(card.features)} klinische Merkmale**\n\n"

    for group_name, group_features in feature_groups.items():
        features_section += f"### {group_name}\n\n"

        # Show all features as numbered list (renders as chips via CSS)
        for i, feature in enumerate(group_features, 1):
            de_name = FEATURE_DISPLAY_NAMES_DE.get(
                feature.name, feature.name.replace("...", "").strip()
            )
            features_section += f"{i}. {de_name}\n"

        features_section += "\n"

    # Build model description section
    model_description = "\n## 🤖 Modellbeschreibung\n\n"
    model_description += "**Random Forest Classifier:** Ensemble von Entscheidungsbäumen, nicht-linear, robust gegenüber Ausreißern und geeignet für heterogene Patient:innenmerkmale\n\n"
    # Use training description and dataset size from JSON metadata when available
    training_desc = None
    dataset_size = None
    if getattr(card, "metadata", None):
        training_desc = card.metadata.get("training_description")
        dataset_size = card.metadata.get("dataset_size")

    model_description += f"- **Trainingsdaten:** {training_desc or 'Pseudonymisierte Beispiel-Patient:innendaten (keine echten Patient:innen)'}\n"
    model_description += f"- **Datensatzgröße:** N={dataset_size if dataset_size is not None else '??'}\n"
    model_description += "- **Train/Test Split:** 80/20 (stratifiziert)\n"

    return f"""\
# HEAR CI Prediction Model

**Version:** {card.version}
**Modelltyp:** {card.model_type}
**Letzte Aktualisierung:** {card.last_updated}
{model_description}
---

## ✓ Bestimmungsgemäße Verwendung

**Zweck:**

{chr(10).join(f"- {x}" for x in card.intended_use)}

**Nicht vorgesehen für:**

{chr(10).join(f"- {x}" for x in card.not_intended_for)}

---

## ⚠️ Einschränkungen

{chr(10).join(f"- {x}" for x in card.limitations)}

---

## 💡 Empfehlungen

{chr(10).join(f"- {x}" for x in card.recommendations)}

---
{metrics_section}
---
{features_section}
---

## 🧠 Interpretierbarkeit / XAI

- **SHAP Feature Importance** wird genutzt, um den Einfluss jeder Variable auf die Vorhersage zu bewerten
- **Wichtigste Einflussfaktoren:** Alter, Beginn der Hörminderung, CI-Typ, Bildgebungsergebnisse, Hörverlust OP-Ohr
- **Visualisierung:** Interaktive Wasserfall- und Force-Plots im Frontend ermöglichen Nachvollziehbarkeit und kritische Bewertung jeder Vorhersage
"""


def _render_model_card_markdown_en() -> str:
    """Build an English Markdown string from the loaded ModelCard."""
    card = load_model_card()

    # Build metrics section only if metrics are available
    metrics_section = ""
    if card.metrics and any(
        [
            card.metrics.accuracy,
            card.metrics.precision,
            card.metrics.recall,
            card.metrics.f1_score,
            card.metrics.roc_auc,
        ]
    ):
        dataset_size = (
            card.metadata.get("dataset_size")
            if getattr(card, "metadata", None)
            else None
        )
        ds_label = f"N={dataset_size}" if dataset_size else "N=?"
        metrics_section = "\n## 📊 Performance / Evaluation\n\n"
        # Render as vertical numbered list: 1) Train/Test set, 2) Metrics combined
        metrics_section += f'1. <strong class="text-primary">Training/Test Set:</strong> 80/20 split ({ds_label})\n\n'

        parts_en: list[str] = []
        if card.metrics.accuracy is not None:
            parts_en.append(
                f'<strong class="text-primary">Accuracy:</strong> {card.metrics.accuracy:.2%}'
            )
        if card.metrics.roc_auc is not None:
            parts_en.append(f"**ROC-AUC:** {card.metrics.roc_auc:.2f}")
        if card.metrics.recall is not None:
            parts_en.append(f"**Sensitivity (Recall):** {card.metrics.recall:.2%}")
        if card.metrics.precision is not None:
            parts_en.append(
                f"**Specificity (Precision):** {card.metrics.precision:.2%}"
            )
        if card.metrics.f1_score is not None:
            parts_en.append(
                f'<strong class="text-primary">F1-Score:</strong> {card.metrics.f1_score:.2f}'
            )

        metrics_combined_en = (
            " | ".join(parts_en) if parts_en else "Metrics not available"
        )
        metrics_section += f"2. {metrics_combined_en}\n\n"
        metrics_section += "\n> **Note:** These figures are for guidance only and should not be used as the sole basis for decision-making.\n"

    # Group features
    feature_groups = _group_features(card.features)

    # Map German group names to English
    group_name_map = {
        "👤 Demografie": "👤 Demographics",
        "🗣️ Sprache & Kommunikation": "🗣️ Language & Communication",
        "👨‍👩‍👧 Familienanamnese": "👨‍👩‍👧 Family History",
        "🩺 Präoperative Symptome": "🩺 Preoperative Symptoms",
        "🔬 Bildgebung": "🔬 Imaging",
        "📊 Objektive Messungen": "📊 Objective Measurements",
        "👂 Hörstatus – Operiertes Ohr": "👂 Hearing Status – Operated Ear",
        "👂 Hörstatus – Gegenohr": "👂 Hearing Status – Contralateral Ear",
        "⚕️ Behandlung & Outcome": "⚕️ Treatment & Outcome",
    }

    features_section = "\n## 📋 Features\n\n"
    features_section += f"**Total: {len(card.features)} clinical features**\n\n"

    for group_name, group_features in feature_groups.items():
        en_group_name = group_name_map.get(group_name, group_name)
        features_section += f"### {en_group_name}\n\n"

        # Show all features with English names
        for i, feature in enumerate(group_features, 1):
            en_name = FEATURE_TRANSLATIONS_DE_EN.get(
                feature.name, feature.name.replace("...", "").strip()
            )
            features_section += f"{i}. {en_name}\n"

        features_section += "\n"

    # Build model description section
    model_description = "\n## 🤖 Model Description\n\n"
    model_description += "**Random Forest Classifier:** Ensemble of decision trees, non-linear, robust to outliers and suitable for heterogeneous patient characteristics\n\n"
    training_desc = None
    dataset_size = None
    if getattr(card, "metadata", None):
        training_desc = card.metadata.get("training_description")
        dataset_size = card.metadata.get("dataset_size")

    model_description += f"- **Training Data:** {training_desc or 'Pseudonymized example patient data (not real patients)'}\n"
    model_description += f"- **Dataset Size:** N={dataset_size if dataset_size is not None else '??'} patients\n"
    model_description += "- **Train/Test Split:** 80/20 (stratified)\n"

    # Translate intended use
    intended_use_en = [
        "Support physicians in assessing the probability of success of a cochlear implant",
        "Decision support tool for planning CI operations",
        "Educational tool for demonstrating XAI methods in clinical decision-making",
    ]

    not_intended_en = [
        "Autonomous clinical decisions without medical evaluation",
        "Use outside the validated patient population",
        "Legal or administrative decisions",
        "Patients under 18 years of age",
    ]

    # Use dataset size where possible; fall back to a generic phrasing
    ds = dataset_size if dataset_size is not None else "??"
    limitations_en = [
        f"Model is based on a limited dataset (N={ds})",
        "Not validated outside the training population (University Hospital Essen)",
        "Predictions are supportive indicators, not deterministic results",
        "Possible biases regarding age groups, gender, and type of hearing loss",
        "Model performance may vary for edge cases not represented in training",
        "Predictions with missing or incomplete data are less reliable",
        "SHAP interpretations show relative influences, not absolute causality",
    ]

    recommendations_en = [
        "Use only as a support tool – human medical judgment takes precedence",
        "Always interpret results in clinical context and considering patient history",
        "Use SHAP explanations to understand and critically evaluate predictions",
        "Regular evaluation and model updates recommended (e.g., every 6 months)",
        "For unexpected predictions: manually verify input data",
    ]

    return f"""\
# HEAR CI Prediction Model

**Version:** {card.version}
**Model Type:** {card.model_type}
**Last Updated:** {card.last_updated}
{model_description}
---

## ✓ Intended Use

**Purpose:**

{chr(10).join(f"- {x}" for x in intended_use_en)}

**Not intended for:**

{chr(10).join(f"- {x}" for x in not_intended_en)}

---

## ⚠️ Limitations

{chr(10).join(f"- {x}" for x in limitations_en)}

---

## 💡 Recommendations

{chr(10).join(f"- {x}" for x in recommendations_en)}

---
{metrics_section}
---
{features_section}
---

## 🧠 Interpretability / XAI

- **SHAP Feature Importance** is used to evaluate the influence of each variable on the prediction
- **Most important factors:** Age, Onset of hearing loss, CI type, Imaging results, Hearing loss operated ear
- **Visualization:** Interactive waterfall and force plots in the frontend enable traceability and critical evaluation of each prediction
"""


def _group_features(features: list) -> dict[str, list]:
    """Group features by category based on naming patterns."""
    groups: dict[str, list] = {
        "👤 Demografie": [],
        "🗣️ Sprache & Kommunikation": [],
        "👨‍👩‍👧 Familienanamnese": [],
        "🩺 Präoperative Symptome": [],
        "🔬 Bildgebung": [],
        "📊 Objektive Messungen": [],
        "👂 Hörstatus – Operiertes Ohr": [],
        "👂 Hörstatus – Gegenohr": [],
        "⚕️ Behandlung & Outcome": [],
    }

    for feature in features:
        name = feature.name
        # Demografie
        if any(x in name for x in ["Geschlecht", "Alter", "Operierte Seiten"]):
            groups["👤 Demografie"].append(feature)
        # Sprache & Kommunikation
        elif any(
            x in name
            for x in [
                "Primäre Sprache",
                "Weitere Sprachen",
                "Sprachbarriere",
                "non-verbal",
            ]
        ):
            groups["🗣️ Sprache & Kommunikation"].append(feature)
        # Familienanamnese
        elif any(x in name for x in ["Eltern m.", "Geschwister m."]):
            groups["👨‍👩‍👧 Familienanamnese"].append(feature)
        # Präoperative Symptome
        elif "Symptome präoperativ" in name:
            groups["🩺 Präoperative Symptome"].append(feature)
        # Bildgebung
        elif "Bildgebung" in name:
            groups["🔬 Bildgebung"].append(feature)
        # Objektive Messungen
        elif "Objektive Messungen" in name:
            groups["📊 Objektive Messungen"].append(feature)
        # Hörstatus – Gegenohr (must come before Operiertes Ohr check)
        elif "Gegenohr" in name:
            groups["👂 Hörstatus – Gegenohr"].append(feature)
        # Hörstatus – Operiertes Ohr
        elif "Diagnose.Höranamnese" in name:
            groups["👂 Hörstatus – Operiertes Ohr"].append(feature)
        # Behandlung & Outcome (CI, outcome measures, time interval)
        elif any(
            x in name
            for x in [
                "Behandlung",
                "CI Implantationstyp",
                "outcome_measurments",
                "Abstand (Tage)",
            ]
        ):
            groups["⚕️ Behandlung & Outcome"].append(feature)

    # Remove empty groups
    return {k: v for k, v in groups.items() if v}


@router.get("", response_class=PlainTextResponse)
def get_model_card(lang: str = Query("de", description="Language: 'de' or 'en'")):
    """Return the model card as plain Markdown (consumed by the frontend)."""
    if lang.lower() == "en":
        return _render_model_card_markdown_en()
    return _render_model_card_markdown_de()


@router.get("/markdown")
def get_model_card_markdown(
    lang: str = Query("de", description="Language: 'de' or 'en'"),
):
    """Return the model card wrapped in a JSON object (legacy)."""
    if lang.lower() == "en":
        return {"markdown": _render_model_card_markdown_en()}
    return {"markdown": _render_model_card_markdown_de()}
