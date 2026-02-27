import copy
import json
import pathlib

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
    "Diagnose.Höranamnese.Hörminderung operiertes Ohr...": "Hearing Loss",
    "Diagnose.Höranamnese.Versorgung operiertes Ohr...": "Hearing Aid / Device",
    "Diagnose.Höranamnese.Zeitpunkt des Hörverlusts (OP-Ohr)...": "Onset Time of Hearing Loss",
    "Diagnose.Höranamnese.Erwerbsart...": "Hearing Loss Acquisition Type",
    "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "Onset of Hearing Loss",
    "Diagnose.Höranamnese.Hochgradige Hörminderung oder Taubheit (OP-Ohr)...": "Severe Hearing Loss or Deafness",
    "Diagnose.Höranamnese.Ursache....Ursache...": "Etiology / Cause of Hearing Loss",
    "Diagnose.Höranamnese.Art der Hörstörung...": "Type of Hearing Disorder",
    "Diagnose.Höranamnese.Hörminderung Gegenohr...": "Hearing Loss",
    "Diagnose.Höranamnese.Versorgung Gegenohr...": "Hearing Device",
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
    "Symptome präoperativ.Geschmack...": "Geschmacksstörung",
    "Symptome präoperativ.Tinnitus...": "Tinnitus",
    "Symptome präoperativ.Schwindel...": "Schwindel",
    "Symptome präoperativ.Otorrhoe...": "Otorrhoe",
    "Symptome präoperativ.Kopfschmerzen...": "Kopfschmerzen",
    "Bildgebung, präoperativ.Typ...": "Bildgebung: Typ",
    "Bildgebung, präoperativ.Befunde...": "Bildgebung: Befund",
    "Objektive Messungen.OAE (TEOAE/DPOAE)...": "OAE",
    "Objektive Messungen.LL...": "LL",
    "Objektive Messungen.4000 Hz...": "4000 Hz",
    "Diagnose.Höranamnese.Hörminderung operiertes Ohr...": "Hörminderung",
    "Diagnose.Höranamnese.Versorgung operiertes Ohr...": "Versorgung",
    "Diagnose.Höranamnese.Zeitpunkt des Hörverlusts (OP-Ohr)...": "Zeitpunkt des Hörverlusts",
    "Diagnose.Höranamnese.Erwerbsart...": "Erwerbsart",
    "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "Beginn der Hörminderung",
    "Diagnose.Höranamnese.Hochgradige Hörminderung oder Taubheit (OP-Ohr)...": "Hochgradige Hörminderung / Taubheit",
    "Diagnose.Höranamnese.Ursache....Ursache...": "Ursache der Hörminderung",
    "Diagnose.Höranamnese.Art der Hörstörung...": "Art der Hörstörung",
    "Diagnose.Höranamnese.Hörminderung Gegenohr...": "Hörminderung",
    "Diagnose.Höranamnese.Versorgung Gegenohr...": "Versorgung",
    "Behandlung/OP.CI Implantation": "Behandlung/OP.CI Implantation",
    "outcome_measurments.pre.measure.": "Outcome.Präoperativ",
    "abstand": "Outcome.Abstand (Tage)",
}


def _render_model_card_markdown_de() -> str:
    """Build a German Markdown string from the loaded ModelCard."""
    card = load_model_card()
    meta = card.metadata or {}

    dataset_size = meta.get("dataset_size")
    ds_label = f"N={dataset_size}" if dataset_size else "N=?"
    features_count = meta.get("features_count") or len(card.features)
    training_date = meta.get("training_date", "")
    validation_strategy = meta.get("validation_strategy", "80/20 Stratifiziert")
    training_desc = meta.get("training_description") or "Gemäß DSGVO pseudonymisiert"
    hyperparams: dict = meta.get("hyperparameters") or {}
    ethical_fairness = meta.get("ethical_fairness", "")
    ethical_transparency = meta.get("ethical_transparency", "")
    changelog = meta.get("changelog", "")

    # ── Model Description ──────────────────────────────────────────────────────
    model_description = "\n## 🤖 Modellbeschreibung\n\n"
    model_description += (
        "**Random Forest Classifier** – Ensemble von Entscheidungsbäumen: "
        "nicht-linear, robust gegenüber Ausreißern und geeignet für heterogene "
        "klinische Merkmale.\n\n"
    )
    model_description += "| Eigenschaft | Wert |\n"
    model_description += "|---|---|\n"
    model_description += f"| Trainingsdaten | {training_desc} |\n"
    model_description += f"| Datensatzgröße | {ds_label} Patient:innen |\n"
    if training_date:
        model_description += f"| Trainingsdatum | {training_date} |\n"
    model_description += f"| Validierungsstrategie | {validation_strategy} |\n"
    model_description += f"| Anzahl Merkmale | {features_count} |\n"
    model_description += "\n"

    # ── Hyperparameter table ───────────────────────────────────────────────────
    if hyperparams:
        max_depth_val = hyperparams.get("max_depth")
        max_depth_disp = (
            str(max_depth_val) if max_depth_val is not None else "unbegrenzt"
        )
        model_description += "### ⚙️ Hyperparameter\n\n"
        model_description += "| Parameter | Wert |\n"
        model_description += "|---|---|\n"
        model_description += (
            f"| n\\_estimators | {hyperparams.get('n_estimators', '?')} |\n"
        )
        model_description += f"| max\\_depth | {max_depth_disp} |\n"
        model_description += (
            f"| min\\_samples\\_split | {hyperparams.get('min_samples_split', '?')} |\n"
        )
        model_description += (
            f"| class\\_weight | {hyperparams.get('class_weight', '?')} |\n"
        )
        model_description += (
            f"| random\\_state | {hyperparams.get('random_state', '?')} |\n"
        )
        model_description += "\n"

    # ── Metrics table ──────────────────────────────────────────────────────────
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
        metrics_section = "\n## 📊 Leistung / Bewertung\n\n"
        metrics_section += (
            f"*Bewertungsgrundlage: 80/20 Train-Test-Split ({ds_label})*\n\n"
        )
        metrics_section += "| Metrik | Ergebnis (Testsatz) |\n"
        metrics_section += "|---|---|\n"
        if card.metrics.accuracy is not None:
            metrics_section += (
                f"| **Genauigkeit (Accuracy)** | **{card.metrics.accuracy:.2%}** |\n"
            )
        if card.metrics.f1_score is not None:
            metrics_section += f"| **F1-Score** | **{card.metrics.f1_score:.2f}** |\n"
        if card.metrics.roc_auc is not None:
            metrics_section += f"| ROC-AUC | {card.metrics.roc_auc:.2f} |\n"
        if card.metrics.recall is not None:
            metrics_section += (
                f"| Sensitivität (Recall) | {card.metrics.recall:.2%} |\n"
            )
        if card.metrics.precision is not None:
            metrics_section += (
                f"| Spezifität (Precision) | {card.metrics.precision:.2%} |\n"
            )
        metrics_section += "\n> **Hinweis:** Zahlen dienen zur Orientierung und ersetzen nicht die klinische Urteilsfähigkeit.\n"

    # ── Features ───────────────────────────────────────────────────────────────
    feature_groups = _group_features(card.features)
    features_section = "\n## 📋 Merkmale\n\n"
    features_section += f"**Gesamt: {len(card.features)} klinische Merkmale**\n\n"
    for group_name, group_features in feature_groups.items():
        features_section += f"### {group_name}\n\n"
        for i, feature in enumerate(group_features, 1):
            de_name = FEATURE_DISPLAY_NAMES_DE.get(
                feature.name, feature.name.replace("...", "").strip()
            )
            features_section += f"{i}. {de_name}\n"
        features_section += "\n"

    # ── Ethical considerations ─────────────────────────────────────────────────
    ethics_section = "\n## 🛡️ Ethische Aspekte\n\n"
    if ethical_fairness:
        ethics_section += f"- **Fairness:** {ethical_fairness}\n"
    ethics_section += f"- **Datenschutz:** {training_desc}\n"
    if ethical_transparency:
        ethics_section += f"- **Transparenz:** {ethical_transparency}\n"

    # ── Changelog ─────────────────────────────────────────────────────────────
    changelog_section = ""
    if changelog:
        changelog_section = f"\n---\n\n## 📝 Versionshinweis\n\n> {changelog}\n"

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
{ethics_section}
---

## 🧠 Interpretierbarkeit / XAI

- **SHAP Feature Importance** bewertet den Beitrag jedes Merkmals zur Vorhersage
- **Einflussfaktoren:** Alter, Beginn der Hörminderung, CI-Typ, Bildgebung, Hörverlust OP-Ohr
- **Visualisierung:** Interaktive Wasserfall- und Force-Plots ermöglichen eine nachvollziehbare Bewertung jeder Vorhersage
{changelog_section}"""


def _render_model_card_markdown_en() -> str:
    """Build an English Markdown string from the loaded ModelCard."""
    card = load_model_card()
    meta = card.metadata or {}

    dataset_size = meta.get("dataset_size")
    ds_label = f"N={dataset_size}" if dataset_size else "N=?"
    features_count = meta.get("features_count") or len(card.features)
    training_date = meta.get("training_date", "")
    validation_strategy = meta.get("validation_strategy", "80/20 Stratified")
    training_desc = (
        meta.get("training_description") or "Pseudonymised in accordance with GDPR"
    )
    hyperparams: dict = meta.get("hyperparameters") or {}
    ethical_fairness = meta.get("ethical_fairness", "")
    ethical_transparency = meta.get("ethical_transparency", "")
    changelog = meta.get("changelog", "")

    # ── Model Description ──────────────────────────────────────────────────────
    model_description = "\n## 🤖 Model Description\n\n"
    model_description += (
        "**Random Forest Classifier** – Ensemble of decision trees: "
        "non-linear, robust to outliers and suitable for heterogeneous "
        "clinical features.\n\n"
    )
    model_description += "| Property | Value |\n"
    model_description += "|---|---|\n"
    model_description += f"| Training Data | {training_desc} |\n"
    model_description += f"| Dataset Size | {ds_label} patients |\n"
    if training_date:
        model_description += f"| Training Date | {training_date} |\n"
    model_description += f"| Validation Strategy | {validation_strategy} |\n"
    model_description += f"| Number of Features | {features_count} |\n"
    model_description += "\n"

    # ── Hyperparameter table ───────────────────────────────────────────────────
    if hyperparams:
        max_depth_val = hyperparams.get("max_depth")
        max_depth_disp = (
            str(max_depth_val) if max_depth_val is not None else "unlimited"
        )
        model_description += "### ⚙️ Hyperparameters\n\n"
        model_description += "| Parameter | Value |\n"
        model_description += "|---|---|\n"
        model_description += (
            f"| n\\_estimators | {hyperparams.get('n_estimators', '?')} |\n"
        )
        model_description += f"| max\\_depth | {max_depth_disp} |\n"
        model_description += (
            f"| min\\_samples\\_split | {hyperparams.get('min_samples_split', '?')} |\n"
        )
        model_description += (
            f"| class\\_weight | {hyperparams.get('class_weight', '?')} |\n"
        )
        model_description += (
            f"| random\\_state | {hyperparams.get('random_state', '?')} |\n"
        )
        model_description += "\n"

    # ── Metrics table ──────────────────────────────────────────────────────────
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
        metrics_section = "\n## 📊 Performance / Evaluation\n\n"
        metrics_section += (
            f"*Evaluation basis: 80/20 train-test split ({ds_label})*\n\n"
        )
        metrics_section += "| Metric | Result (Test Set) |\n"
        metrics_section += "|---|---|\n"
        if card.metrics.accuracy is not None:
            metrics_section += f"| **Accuracy** | **{card.metrics.accuracy:.2%}** |\n"
        if card.metrics.f1_score is not None:
            metrics_section += f"| **F1-Score** | **{card.metrics.f1_score:.2f}** |\n"
        if card.metrics.roc_auc is not None:
            metrics_section += f"| ROC-AUC | {card.metrics.roc_auc:.2f} |\n"
        if card.metrics.recall is not None:
            metrics_section += f"| Sensitivity (Recall) | {card.metrics.recall:.2%} |\n"
        if card.metrics.precision is not None:
            metrics_section += (
                f"| Specificity (Precision) | {card.metrics.precision:.2%} |\n"
            )
        metrics_section += "\n> **Note:** These figures are for guidance only and should not be used as the sole basis for clinical decision-making.\n"

    # ── Features ───────────────────────────────────────────────────────────────
    feature_groups = _group_features(card.features)

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
        for i, feature in enumerate(group_features, 1):
            en_name = FEATURE_TRANSLATIONS_DE_EN.get(
                feature.name, feature.name.replace("...", "").strip()
            )
            features_section += f"{i}. {en_name}\n"
        features_section += "\n"

    # ── Ethical considerations ─────────────────────────────────────────────────
    ethics_section = "\n## 🛡️ Ethical Considerations\n\n"
    if ethical_fairness:
        ethics_section += f"- **Fairness:** {ethical_fairness}\n"
    ethics_section += f"- **Privacy:** {training_desc}\n"
    if ethical_transparency:
        ethics_section += f"- **Transparency:** {ethical_transparency}\n"

    # ── Changelog ─────────────────────────────────────────────────────────────
    changelog_section = ""
    if changelog:
        changelog_section = f"\n---\n\n## 📝 Version Notes\n\n> {changelog}\n"

    # ── Static lists (localised hardcoded) ────────────────────────────────────
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
{ethics_section}
---

## 🧠 Interpretability / XAI

- **SHAP Feature Importance** evaluates each feature's contribution to the prediction
- **Key factors:** Age, Onset of hearing loss, CI type, Imaging results, Hearing loss operated ear
- **Visualization:** Interactive waterfall and force plots enable traceability and critical evaluation of each prediction
{changelog_section}"""


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


def _build_feature_groups_json(lang: str) -> dict:
    """Build grouped features dict for the JSON endpoint."""
    card = load_model_card()
    feature_groups = _group_features(card.features)
    total = len(card.features)

    group_name_map_en = {
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

    result: dict[str, list[str]] = {}
    for group_name, features in feature_groups.items():
        display_group = (
            group_name_map_en.get(group_name, group_name)
            if lang == "en"
            else group_name
        )
        names: list[str] = []
        for f in features:
            if lang == "en":
                names.append(
                    FEATURE_TRANSLATIONS_DE_EN.get(
                        f.name, f.name.replace("...", "").strip()
                    )
                )
            else:
                names.append(
                    FEATURE_DISPLAY_NAMES_DE.get(
                        f.name, f.name.replace("...", "").strip()
                    )
                )
        result[display_group] = names

    return {"groups": result, "total": total}


@router.get("/json")
def get_model_card_json(lang: str = Query("de", description="Language: 'de' or 'en'")):
    """Return structured model card JSON, with text fields in the requested language."""
    json_path = (
        pathlib.Path(__file__).parent.parent.parent
        / "config"
        / "model_cards"
        / "v3_randomforest_2026-02-17.json"
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # ── Feature groups & XAI (both languages) ──────────────────────────────
    feature_data = _build_feature_groups_json(lang.lower())

    if lang.lower() != "en":
        data["name"] = "HEAR CI Prognosemodell"
        data["status"] = "aktiv"
        data["feature_groups"] = feature_data["groups"]
        data["features_total"] = feature_data["total"]
        return data

    # ── English overrides ──────────────────────────────────────────────────────
    en = copy.deepcopy(data)
    en["name"] = "HEAR CI Prediction Model"
    en["model_type"] = "RandomForestClassifier"
    en["status"] = "active"

    en["training"]["validation_strategy"] = "Stratified 80/20 train test split"

    en["intended_use"] = [
        "Support physicians in estimating the probability of cochlear implant success",
        "Decision support tool for planning CI surgeries",
        "Educational tool to demonstrate XAI methods in clinical decision-making",
    ]
    en["not_intended_for"] = [
        "Autonomous clinical decisions without medical evaluation",
        "Use outside the validated patient population",
        "Legal or administrative decisions",
        "Patients under 18 years of age",
    ]
    en["limitations"] = [
        "Model is based on a limited dataset (N=235)",
        "Not validated outside the training population",
        "Predictions are supportive indicators, not deterministic outcomes",
        "Possible biases regarding age groups, gender and type of hearing loss",
        "Model performance may vary for edge cases not represented in training",
        "Predictions less reliable with missing or incomplete data",
        "SHAP interpretations show relative influence, not absolute causality",
    ]
    en["recommendations"] = [
        "Use only as a support tool – human medical judgment takes precedence",
        "Always interpret results in clinical context and considering patient history",
        "Use SHAP explanations to understand and critically evaluate predictions",
        "Regular evaluation and model updates recommended (e.g., every 6 months)",
        "For unexpected predictions: manually verify input data",
    ]
    en["ethical_considerations"] = {
        "fairness": "Model was tested for bias in age groups and gender. No significant discrimination detected.",
        "privacy": "All patient data is pseudonymised in accordance with GDPR (sample data only, no real patients).",
        "transparency": "SHAP explanations are provided for all predictions to ensure traceability.",
    }
    en["changelog"] = (
        "Improved hyperparameters and class weighting for imbalanced data. "
        "Accuracy improved from 0.74 (v2) to 0.76 (v3)."
    )

    en["feature_groups"] = feature_data["groups"]
    en["features_total"] = feature_data["total"]

    return en


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
