"""
Targeted tests for low-coverage modules:
  - app/api/routes/features.py        (was 38 %)
  - app/core/feature_catalog.py       (was 19 %)
  - app/api/routes/predict_batch.py   (was 53 %)

Approach: call the functions / endpoints directly and assert sensible outputs.
lru_cache is cleared before each class so every internal branch is exercised.
"""

from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _make_csv(rows: list[dict]) -> bytes:
    """Build a minimal CSV bytes object from a list of dicts."""
    if not rows:
        return b""
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(h, "")) for h in headers))
    return "\n".join(lines).encode()


# ──────────────────────────────────────────────────────────────────────────────
# feature_catalog.py
# ──────────────────────────────────────────────────────────────────────────────


class TestFeatureCatalogLoader:
    """Direct unit tests for app.core.feature_catalog functions."""

    def setup_method(self):
        """Clear all lru_caches so every test hits the actual code path."""
        from app.core import feature_catalog

        for fn_name in (
            "load_feature_definitions",
            "_definitions_index",
            "load_feature_locales",
            "load_section_locales",
        ):
            fn = getattr(feature_catalog, fn_name, None)
            if fn and hasattr(fn, "cache_clear"):
                fn.cache_clear()

    def test_load_feature_definitions_returns_list(self):
        from app.core.feature_catalog import load_feature_definitions

        defs = load_feature_definitions()
        assert isinstance(defs, list)
        assert len(defs) > 0

    def test_load_feature_definitions_entries_have_required_keys(self):
        from app.core.feature_catalog import load_feature_definitions

        defs = load_feature_definitions()
        for entry in defs:
            assert "raw" in entry
            assert "normalized" in entry
            assert "description" in entry

    def test_load_feature_definitions_cached(self):
        from app.core.feature_catalog import load_feature_definitions

        first = load_feature_definitions()
        second = load_feature_definitions()
        assert first is second  # lru_cache returns same object

    def test_load_feature_definitions_missing_file(self, tmp_path, monkeypatch):
        """Simulate missing definitions file → should return []."""
        from app.core import feature_catalog

        monkeypatch.setattr(
            feature_catalog, "_definitions_path", lambda: tmp_path / "nonexistent.json"
        )
        feature_catalog.load_feature_definitions.cache_clear()
        result = feature_catalog.load_feature_definitions()
        assert result == []

    def test_load_feature_definitions_invalid_json(self, tmp_path, monkeypatch):
        """Simulate corrupt JSON → should return []."""
        from app.core import feature_catalog

        bad = tmp_path / "bad.json"
        bad.write_text("not valid json", encoding="utf-8")
        monkeypatch.setattr(feature_catalog, "_definitions_path", lambda: bad)
        feature_catalog.load_feature_definitions.cache_clear()
        result = feature_catalog.load_feature_definitions()
        assert result == []

    def test_load_feature_definitions_non_dict_json(self, tmp_path, monkeypatch):
        """JSON is a list instead of dict → should return []."""
        from app.core import feature_catalog

        bad = tmp_path / "bad.json"
        bad.write_text("[1, 2, 3]", encoding="utf-8")
        monkeypatch.setattr(feature_catalog, "_definitions_path", lambda: bad)
        feature_catalog.load_feature_definitions.cache_clear()
        result = feature_catalog.load_feature_definitions()
        assert result == []

    def test_load_feature_definitions_skips_missing_raw(self, tmp_path, monkeypatch):
        """Entries without raw/normalized are skipped."""
        from app.core import feature_catalog

        data = {"features": [{"description": "no raw or normalized"}]}
        f = tmp_path / "defs.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setattr(feature_catalog, "_definitions_path", lambda: f)
        feature_catalog.load_feature_definitions.cache_clear()
        result = feature_catalog.load_feature_definitions()
        assert result == []

    def test_load_feature_definitions_optional_fields_included(
        self, tmp_path, monkeypatch
    ):
        """Optional fields (options, section, type, etc.) are included when present."""
        from app.core import feature_catalog

        data = {
            "features": [
                {
                    "raw": "TestFeature",
                    "normalized": "test_feature",
                    "description": "A test",
                    "options": [{"value": "A"}],
                    "section": "Demo",
                    "input_type": "text",
                    "type": "string",
                    "multiple": False,
                    "other_field": "test_other",
                    "ui_only": True,
                }
            ]
        }
        f = tmp_path / "defs.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setattr(feature_catalog, "_definitions_path", lambda: f)
        feature_catalog.load_feature_definitions.cache_clear()
        result = feature_catalog.load_feature_definitions()
        assert len(result) == 1
        entry = result[0]
        assert entry["section"] == "Demo"
        assert entry["type"] == "string"
        assert entry["ui_only"] is True
        assert entry["other_field"] == "test_other"

    def test_definitions_index_returns_dict_by_raw(self):
        from app.core.feature_catalog import _definitions_index

        _definitions_index.cache_clear()
        idx = _definitions_index()
        assert isinstance(idx, dict)
        # At least one entry should exist
        assert len(idx) > 0
        for raw, entry in idx.items():
            assert entry["raw"] == raw

    def test_load_feature_locales_english(self):
        from app.core.feature_catalog import load_feature_locales

        load_feature_locales.cache_clear()
        labels = load_feature_locales("en")
        assert isinstance(labels, dict)

    def test_load_feature_locales_german(self):
        from app.core.feature_catalog import load_feature_locales

        load_feature_locales.cache_clear()
        labels = load_feature_locales("de")
        assert isinstance(labels, dict)

    def test_load_feature_locales_unknown_falls_back_to_en(self):
        from app.core.feature_catalog import load_feature_locales

        load_feature_locales.cache_clear()
        labels = load_feature_locales("zz")  # non-existent locale
        # Should fall back to en or return empty; in both cases a dict
        assert isinstance(labels, dict)

    def test_load_feature_locales_missing_file_returns_empty(
        self, tmp_path, monkeypatch
    ):
        from app.core import feature_catalog

        monkeypatch.setattr(
            feature_catalog, "_locales_dir", lambda: tmp_path / "absent"
        )
        feature_catalog.load_feature_locales.cache_clear()
        result = feature_catalog.load_feature_locales("en")
        assert result == {}

    def test_load_feature_locales_bad_json_returns_empty(self, tmp_path, monkeypatch):
        from app.core import feature_catalog

        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()
        (locales_dir / "en.json").write_text("INVALID", encoding="utf-8")
        monkeypatch.setattr(feature_catalog, "_locales_dir", lambda: locales_dir)
        feature_catalog.load_feature_locales.cache_clear()
        result = feature_catalog.load_feature_locales("en")
        assert result == {}

    def test_load_feature_locales_non_dict_json_returns_empty(
        self, tmp_path, monkeypatch
    ):
        from app.core import feature_catalog

        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()
        (locales_dir / "en.json").write_text("[1, 2]", encoding="utf-8")
        monkeypatch.setattr(feature_catalog, "_locales_dir", lambda: locales_dir)
        feature_catalog.load_feature_locales.cache_clear()
        result = feature_catalog.load_feature_locales("en")
        assert result == {}

    def test_load_section_locales_english(self):
        from app.core.feature_catalog import load_section_locales

        load_section_locales.cache_clear()
        sections = load_section_locales("en")
        assert isinstance(sections, dict)

    def test_load_section_locales_german(self):
        from app.core.feature_catalog import load_section_locales

        load_section_locales.cache_clear()
        sections = load_section_locales("de")
        assert isinstance(sections, dict)

    def test_load_section_locales_missing_falls_back_to_en(self):
        from app.core.feature_catalog import load_section_locales

        load_section_locales.cache_clear()
        sections = load_section_locales("fr")
        assert isinstance(sections, dict)

    def test_load_section_locales_bad_json_returns_empty(self, tmp_path, monkeypatch):
        from app.core import feature_catalog

        sec_dir = tmp_path / "sections"
        sec_dir.mkdir()
        (sec_dir / "en.json").write_text("{invalid}", encoding="utf-8")
        monkeypatch.setattr(feature_catalog, "_section_locales_dir", lambda: sec_dir)
        feature_catalog.load_section_locales.cache_clear()
        result = feature_catalog.load_section_locales("en")
        assert result == {}

    def test_load_section_locales_missing_returns_empty(self, tmp_path, monkeypatch):
        from app.core import feature_catalog

        monkeypatch.setattr(
            feature_catalog, "_section_locales_dir", lambda: tmp_path / "nope"
        )
        feature_catalog.load_section_locales.cache_clear()
        result = feature_catalog.load_section_locales("en")
        assert result == {}

    def test_build_raw_label_map_returns_dict(self):
        from app.core.feature_catalog import _definitions_index, build_raw_label_map

        _definitions_index.cache_clear()
        result = build_raw_label_map("en")
        assert isinstance(result, dict)

    def test_build_raw_label_map_keys_are_raw_names(self):
        from app.core.feature_catalog import (
            _definitions_index,
            build_raw_label_map,
            load_feature_definitions,
        )

        load_feature_definitions.cache_clear()
        _definitions_index.cache_clear()
        result = build_raw_label_map("en")
        defs = load_feature_definitions()
        for entry in defs:
            assert entry["raw"] in result

    def test_build_raw_label_map_german(self):
        from app.core.feature_catalog import _definitions_index, build_raw_label_map

        _definitions_index.cache_clear()
        result = build_raw_label_map("de")
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_normalize_locale(self):
        from app.core.feature_catalog import _normalize_locale

        assert _normalize_locale("en-US") == "en"
        assert _normalize_locale("DE") == "de"
        assert _normalize_locale("") == "en"
        assert _normalize_locale(None) == "en"  # type: ignore[arg-type]


# ──────────────────────────────────────────────────────────────────────────────
# features.py routes
# ──────────────────────────────────────────────────────────────────────────────


class TestFeaturesRoutes:
    """Integration tests for /features/* endpoints via TestClient."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        from app.main import app

        with TestClient(app) as c:
            self._client = c
            yield

    def test_get_definitions_returns_200(self):
        resp = self._client.get("/api/v1/features/definitions")
        assert resp.status_code == 200

    def test_get_definitions_has_features_key(self):
        resp = self._client.get("/api/v1/features/definitions")
        data = resp.json()
        assert "features" in data
        assert isinstance(data["features"], list)

    def test_get_definitions_has_section_order(self):
        resp = self._client.get("/api/v1/features/definitions")
        data = resp.json()
        assert "section_order" in data
        assert isinstance(data["section_order"], list)

    def test_get_definitions_section_order_unique(self):
        resp = self._client.get("/api/v1/features/definitions")
        order = resp.json()["section_order"]
        assert len(order) == len(set(order)), "Section order should have no duplicates"

    def test_get_locales_en_returns_200(self):
        resp = self._client.get("/api/v1/features/locales/en")
        assert resp.status_code == 200

    def test_get_locales_de_returns_200(self):
        resp = self._client.get("/api/v1/features/locales/de")
        assert resp.status_code == 200

    def test_get_locales_response_structure(self):
        resp = self._client.get("/api/v1/features/locales/en")
        data = resp.json()
        assert "language" in data
        assert "labels" in data
        assert "sections" in data
        assert data["language"] == "en"

    def test_get_locales_normalises_locale(self):
        # 'en-US' should be normalised to 'en'
        resp = self._client.get("/api/v1/features/locales/en-US")
        assert resp.status_code == 200
        assert resp.json()["language"] == "en"

    def test_get_locales_unknown_locale(self):
        resp = self._client.get("/api/v1/features/locales/zz")
        assert resp.status_code == 200  # graceful fallback

    def test_get_labels_default_lang(self):
        resp = self._client.get("/api/v1/features/labels")
        assert resp.status_code == 200
        data = resp.json()
        assert "language" in data
        assert "labels" in data
        assert data["language"] == "en"

    def test_get_labels_explicit_de(self):
        resp = self._client.get("/api/v1/features/labels?lang=de")
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "de"

    def test_get_labels_normalises_lang(self):
        resp = self._client.get("/api/v1/features/labels?lang=DE-CH")
        assert resp.status_code == 200
        assert resp.json()["language"] == "de"


# ──────────────────────────────────────────────────────────────────────────────
# predict_batch.py helpers — already partly covered; add endpoint tests
# ──────────────────────────────────────────────────────────────────────────────


class TestPredictBatchEndpoint:
    """Tests for the POST /api/v1/batch/upload endpoint."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Use context-manager form so app lifespan (model_wrapper init) runs."""
        from app.main import app

        with TestClient(app) as c:
            self._client = c
            self._app = app
            yield

    def _csv_file(self, rows: list[dict]) -> dict:
        """Return a files dict suitable for httpx multipart upload."""
        data = _make_csv(rows)
        return {"file": ("test.csv", io.BytesIO(data), "text/csv")}

    def _model_loaded(self) -> bool:
        wrapper = getattr(self._app.state, "model_wrapper", None)
        return wrapper is not None and wrapper.is_loaded()

    def test_upload_no_model_returns_503(self, monkeypatch):
        """When model is not loaded, endpoint must return 503."""
        wrapper = getattr(self._app.state, "model_wrapper", None)
        if wrapper is None:
            pytest.skip("model_wrapper state not available")
        monkeypatch.setattr(wrapper, "is_loaded", lambda: False)
        resp = self._client.post(
            "/api/v1/batch/upload",
            files=self._csv_file([{"Alter [J]": 50, "Geschlecht": "m"}]),
        )
        assert resp.status_code == 503

    def test_upload_empty_csv_returns_empty_results(self):
        """Uploading a CSV with only headers (no data rows) → count=0."""
        if not self._model_loaded():
            pytest.skip("Model not loaded in test environment")
        empty_csv = b"Alter [J],Geschlecht\n"
        resp = self._client.post(
            "/api/v1/batch/upload",
            files={"file": ("empty.csv", io.BytesIO(empty_csv), "text/csv")},
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_upload_invalid_file_returns_400(self):
        """Uploading non-CSV binary blob should return 400."""
        if not self._model_loaded():
            pytest.skip("Model not loaded in test environment")
        bad = b"\x00\x01\x02\x03NOTCSV\xff"
        resp = self._client.post(
            "/api/v1/batch/upload",
            files={"file": ("bad.bin", io.BytesIO(bad), "application/octet-stream")},
        )
        assert resp.status_code in (400, 422)

    def test_upload_valid_row_returns_prediction(self):
        """Upload a single row with minimal required fields."""
        if not self._model_loaded():
            pytest.skip("Model not loaded in test environment")
        rows = [
            {
                "Alter [J]": 45,
                "Geschlecht": "m",
                "Primäre Sprache": "Deutsch",
                "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
                "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
            }
        ]
        resp = self._client.post(
            "/api/v1/batch/upload",
            files=self._csv_file(rows),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "count" in body
        assert "results" in body

    def test_upload_mixed_rows(self):
        """Upload multiple rows; some may fail gracefully."""
        if not self._model_loaded():
            pytest.skip("Model not loaded in test environment")
        rows = [
            {
                "Alter [J]": 45,
                "Geschlecht": "m",
                "Primäre Sprache": "Deutsch",
                "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
                "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
            },
            {
                "Alter [J]": 60,
                "Geschlecht": "w",
                "Primäre Sprache": "Deutsch",
                "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
                "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
            },
        ]
        resp = self._client.post(
            "/api/v1/batch/upload",
            files=self._csv_file(rows),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] >= 0

    def test_upload_persist_flag(self):
        """persist=true should not crash even if DB write fails."""
        if not self._model_loaded():
            pytest.skip("Model not loaded in test environment")
        rows = [
            {
                "Alter [J]": 50,
                "Geschlecht": "m",
                "Primäre Sprache": "Deutsch",
                "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
                "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
            }
        ]
        resp = self._client.post(
            "/api/v1/batch/upload?persist=true",
            files=self._csv_file(rows),
        )
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# predict_batch.py pure helpers (already tested but fill remaining branches)
# ──────────────────────────────────────────────────────────────────────────────


class TestPredictBatchHelpersBranches:
    """Additional branch coverage for _to_bool, _parse_interval_to_years, _normalize_header."""

    def test_to_bool_numeric_one(self):
        from app.api.routes.predict_batch import _to_bool

        assert _to_bool(1) is True

    def test_to_bool_numeric_zero(self):
        from app.api.routes.predict_batch import _to_bool

        assert _to_bool(0) is False

    def test_to_bool_nan_like(self):
        from app.api.routes.predict_batch import _to_bool

        assert _to_bool("nan") is None
        assert _to_bool("none") is None

    def test_to_bool_unknown(self):
        from app.api.routes.predict_batch import _to_bool

        assert _to_bool("maybe") is None

    def test_parse_interval_numeric_string(self):
        from app.api.routes.predict_batch import _parse_interval_to_years

        assert _parse_interval_to_years("3.5") == pytest.approx(3.5)

    def test_parse_interval_unbekannt_variants(self):
        from app.api.routes.predict_batch import _parse_interval_to_years

        assert _parse_interval_to_years("nicht erhoben") is None
        assert _parse_interval_to_years("unbekannt") is None
        assert _parse_interval_to_years("unbekannt/ka") is None

    def test_normalize_header_bom(self):
        from app.api.routes.predict_batch import _normalize_header

        assert _normalize_header("\ufeffAlter") == "alter"

    def test_normalize_header_whitespace(self):
        from app.api.routes.predict_batch import _normalize_header

        assert _normalize_header("  Geschlecht  ") == "geschlecht"
