#!/usr/bin/env python3
"""Demonstrate config-based dataset adapter vs hardcoded adapter.

This script shows the practical benefits of configuration-based adapters:
1. Easy model swapping without code changes
2. Clear feature definitions in JSON
3. Identical results to hardcoded adapters
"""

import sys
from pathlib import Path

import numpy as np

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config_based_adapter import load_dataset_adapter_from_config
from app.core.model_wrapper import ModelWrapper
from app.core.rf_dataset_adapter import RandomForestDatasetAdapter


def demonstrate_config_based_adapter():
    """Show config-based adapter in action."""

    print("=" * 70)
    print("Configuration-Based Dataset Adapter Demo")
    print("=" * 70)

    # Sample patient data
    sample_patient = {
        "Alter [J]": 45,
        "Geschlecht": "w",
        "Primäre Sprache": "Deutsch",
        "Seiten": "L",
        "Symptome präoperativ.Tinnitus...": "ja",
        "Symptome präoperativ.Schwindel...": "nein",
        "outcome_measurments.pre.measure.": 15.0,
        "abstand": 200,
    }

    print("\nSample Patient Data:")
    for key, value in sample_patient.items():
        print(f"  {key}: {value}")

    # 1. Old approach: Hardcoded adapter
    print("\n" + "=" * 70)
    print("[OLD] OLD APPROACH: Hardcoded Adapter")
    print("=" * 70)
    print("Code: RandomForestDatasetAdapter() - 305 lines of hardcoded logic")

    hardcoded_adapter = RandomForestDatasetAdapter()
    X_hardcoded = hardcoded_adapter.preprocess(sample_patient)

    print(f"\n✓ Preprocessed shape: {X_hardcoded.shape}")
    print(f"✓ First 10 features: {X_hardcoded[0, :10]}")

    # 2. New approach: Config-based adapter
    print("\n" + "=" * 70)
    print("[NEW] NEW APPROACH: Config-Based Adapter")
    print("=" * 70)

    config_path = backend_path / "app" / "config" / "random_forest_features.json"
    print(f"Config: {config_path.relative_to(Path.cwd())}")

    config_adapter = load_dataset_adapter_from_config(config_path)
    X_config = config_adapter.preprocess(sample_patient)

    print(f"\n✓ Preprocessed shape: {X_config.shape}")
    print(f"✓ First 10 features: {X_config[0, :10]}")

    # 3. Compare results
    print("\n" + "=" * 70)
    print("Comparison: Hardcoded vs Config-Based")
    print("=" * 70)

    matches = np.allclose(X_hardcoded, X_config, rtol=1e-5)
    print(f"\n✓ Arrays match: {matches}")

    if matches:
        print("IDENTICAL RESULTS - Config-based adapter produces same output!")
    else:
        print("WARNING: Differences detected:")
        diff_indices = np.where(~np.isclose(X_hardcoded, X_config, rtol=1e-5))[1]
        print(f"   Different at indices: {diff_indices}")

    # 4. Show advantages
    print("\n" + "=" * 70)
    print("Advantages of Config-Based Approach")
    print("=" * 70)

    advantages = [
        ("Easy Model Swapping", "Change config file, not Python code"),
        ("Version Control", "JSON configs are easy to review in PRs"),
        ("Auditability", "Feature definitions in single readable file"),
        ("No Code Changes", "Add/modify features without touching Python"),
        ("Multilingual Support", "Aliases for German/English field names"),
        ("Domain-Agnostic", "Works for any dataset/model"),
    ]

    for title, description in advantages:
        print(f"\n✓ {title}")
        print(f"  → {description}")

    # 5. Demonstrate alias resolution
    print("\n" + "=" * 70)
    print("Multilingual Alias Resolution")
    print("=" * 70)

    english_patient = {
        "age": 55,  # Instead of "Alter [J]"
        "gender": "m",  # Instead of "Geschlecht"
        "primary_language": "Deutsch",  # Instead of "Primäre Sprache"
        "implant_side": "R",  # Instead of "Seiten"
    }

    print("\nEnglish aliases:")
    for key, value in english_patient.items():
        print(f"  {key}: {value}")

    X_english = config_adapter.preprocess(english_patient)
    print(f"\n✓ Preprocessed with English aliases: {X_english.shape}")
    print("Aliases automatically resolved to canonical German names!")

    # 6. Show ModelWrapper integration
    print("\n" + "=" * 70)
    print("ModelWrapper Integration")
    print("=" * 70)

    print("\n# OLD: Hardcoded adapter")
    print("wrapper = ModelWrapper()  # Uses RandomForestDatasetAdapter")

    print("\n# NEW: Config-based adapter")
    print('wrapper = ModelWrapper.from_config("app/config/random_forest_features.json")')

    print("\n✓ One-line change for complete flexibility!")

    # 7. Show model swapping example
    print("\n" + "=" * 70)
    print("Model Swapping Example")
    print("=" * 70)

    print("\nScenario: Switch from Random Forest to XGBoost")
    print("\n1. Train new model:")
    print("   xgboost_model.pkl (50 features instead of 39)")

    print("\n2. Create config:")
    print("   config/xgboost_features.json")

    print("\n3. Update environment:")
    print("   export MODEL_PATH=/models/xgboost_model.pkl")
    print("   export FEATURES_CONFIG=config/xgboost_features.json")

    print("\n4. Code change:")
    print("   config = os.getenv('FEATURES_CONFIG', 'config/random_forest_features.json')")
    print("   wrapper = ModelWrapper.from_config(config)")

    print("\nModel swapped without changing feature engineering code!")

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    summary = """
The config-based adapter eliminates hardcoded domain knowledge and enables:

- Easy model swapping (change config file)
- No code changes for new features
- Version-controlled feature definitions
- Domain-agnostic architecture
- Multilingual alias support
- Identical results to hardcoded adapters

This fulfills the extensibility requirement for a truly generic medical AI
prototype that supports arbitrary models and datasets.
"""
    print(summary)


if __name__ == "__main__":
    demonstrate_config_based_adapter()
