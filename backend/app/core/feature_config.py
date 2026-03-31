"""Feature config loader.

Loads `backend/app/config/features.yaml` (if present) and returns a small
structure expected by the rest of the app: `{mapping, categories, metadata}`.

This is intentionally lightweight and tolerant: if the file is missing or
invalid the loader returns `None` so callers fall back to in-code defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _config_path() -> Path:
    # app package root -> go to ../config/features.yaml
    base = Path(__file__).resolve().parent.parent
    return base / "config" / "features.yaml"


def load_feature_config() -> dict[str, Any] | None:
    """Attempt to load and normalize the feature config YAML.

    Returns a dict with keys:
      - mapping: {technical_name: label}
      - categories: {category_label: [technical_name,...]}
      - metadata: {technical_name: {full entry}}

    Returns `None` on any loading/parsing error so callers may fall back.
    """
    p = _config_path()
    if not p.exists():
        return None

    try:
        raw = yaml.safe_load(p.read_text())
        features = raw.get("features") if isinstance(raw, dict) else None
        if not features or not isinstance(features, list):
            return None

        mapping: dict[str, str] = {}
        categories: dict[str, list] = {}
        metadata: dict[str, dict] = {}

        for entry in features:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            label = entry.get("label") or name
            cat = entry.get("category") or "Uncategorized"

            if not name:
                continue

            mapping[name] = label  # type: ignore[assignment]
            metadata[name] = {k: v for k, v in entry.items() if k != "name"}
            categories.setdefault(cat, []).append(name)

        return {"mapping": mapping, "categories": categories, "metadata": metadata}
    except Exception:
        # Keep loader tolerant; callers expect None to mean "no config"
        return None
