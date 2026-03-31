"""Background data generator for SHAP explanations.

This module creates representative background samples that can be used
with SHAP explainers. For pipelines with preprocessing, it generates
both raw and transformed backgrounds.
"""

import logging
import os

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def create_synthetic_background(
    n_samples: int = 50,
    include_transformed: bool = True,
    pipeline: object | None = None,
) -> tuple[pd.DataFrame, np.ndarray | None]:
    """Create synthetic background data for SHAP.

    Args:
        n_samples: Number of background samples to generate
        include_transformed: If True and pipeline provided, also return transformed features
        pipeline: Optional sklearn Pipeline to transform the raw background

    Returns:
        Tuple of (raw_df, transformed_array or None)
    """
    # Define representative values for each feature based on the HEAR project
    # These are typical/median values from the patient population

    rng = np.random.RandomState(42)

    # If a static background CSV is provided in the repo, prefer loading it.
    # This allows using real examples from the project as SHAP background.
    bg_path = os.environ.get(
        "SHAP_BACKGROUND_FILE",
        os.path.join(
            os.path.dirname(__file__), "..", "models", "background_sample.csv"
        ),
    )
    if os.path.exists(bg_path):
        try:
            raw_df = pd.read_csv(bg_path)
            # Drop completely empty rows and columns often present in exported CSVs
            raw_df = raw_df.dropna(how="all")
            raw_df = raw_df.loc[:, raw_df.columns.notna()]
            # Keep at most n_samples
            if len(raw_df) > n_samples:
                raw_df = raw_df.sample(n=n_samples, random_state=42).reset_index(
                    drop=True
                )
            logger.info(
                "Loaded background samples from %s (%d rows)", bg_path, len(raw_df)
            )
        except Exception as e:
            logger.warning(
                "Failed to load background CSV %s: %s - falling back to synthetic",
                bg_path,
                e,
            )
            raw_df = None
    else:
        raw_df = None

    # If we didn't successfully load a background CSV, synthesize representative values
    if raw_df is None:
        # Numeric feature: Age (roughly normal around 45-55)
        ages = rng.normal(loc=50, scale=15, size=n_samples).clip(18, 90).astype(int)

        # Categorical features with realistic distributions
        genders = rng.choice(["m", "w"], size=n_samples, p=[0.45, 0.55])

        languages = rng.choice(
            ["Deutsch", "Englisch", "Andere"], size=n_samples, p=[0.7, 0.2, 0.1]
        )

        onset = rng.choice(
            ["postlingual", "praelingual", "perilingual"],
            size=n_samples,
            p=[0.6, 0.3, 0.1],
        )

        cause = rng.choice(
            ["Unbekannt", "Genetisch", "Lärm", "Meningitis"],
            size=n_samples,
            p=[0.5, 0.25, 0.15, 0.1],
        )

        tinnitus = rng.choice(["ja", "nein"], size=n_samples, p=[0.4, 0.6])

        implant = rng.choice(
            ["Cochlear", "Advanced Bionics", "Med-El"],
            size=n_samples,
            p=[0.5, 0.3, 0.2],
        )

        # Create DataFrame with exact column names from pipeline
        raw_df = pd.DataFrame(
            {
                "Alter [J]": ages,
                "Geschlecht": genders,
                "Primäre Sprache": languages,
                "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": onset,
                "Diagnose.Höranamnese.Ursache....Ursache...": cause,
                "Symptome präoperativ.Tinnitus...": tinnitus,
                "Behandlung/OP.CI Implantation": implant,
            }
        )

    # Transform if pipeline provided
    transformed = None
    if include_transformed and pipeline is not None:
        try:
            # If pipeline has named_steps, get the preprocessor
            if hasattr(pipeline, "named_steps"):
                preprocessor = pipeline.named_steps.get("preprocessor")
                if preprocessor is not None:
                    transformed = preprocessor.transform(raw_df)
                    logger.info(
                        "Created transformed background: %s samples, %s features",
                        transformed.shape[0],
                        transformed.shape[1],
                    )
            else:
                # Try to transform with full pipeline
                transformed = pipeline.transform(raw_df)  # type: ignore[attr-defined]
        except Exception as e:
            logger.warning("Could not transform background data: %s", e)
            transformed = None

    logger.info("Created synthetic background: %s raw samples", len(raw_df))
    return raw_df, transformed


def get_feature_names_from_pipeline(pipeline) -> list | None:
    """Extract feature names from a sklearn pipeline.

    Args:
        pipeline: sklearn Pipeline object

    Returns:
        List of feature names after transformation, or None if unavailable
    """
    try:
        if hasattr(pipeline, "named_steps"):
            preprocessor = pipeline.named_steps.get("preprocessor")
            if preprocessor is not None and hasattr(
                preprocessor, "get_feature_names_out"
            ):
                return list(preprocessor.get_feature_names_out())

        # Fallback: try on pipeline directly
        if hasattr(pipeline, "get_feature_names_out"):
            return list(pipeline.get_feature_names_out())

    except Exception as e:
        logger.debug("Could not extract feature names: %s", e)

    return None
