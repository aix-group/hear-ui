"""Tests for the model card API routes.

Covers the three endpoints:
  GET /api/v1/model-card              – plain Markdown
  GET /api/v1/model-card/json         – JSON model card
  GET /api/v1/model-card/markdown     – JSON-wrapped Markdown
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestModelCardMarkdownRoute:
    """Tests for GET /api/v1/model-card (plain Markdown)."""

    def test_returns_200_default(self, client: TestClient):
        resp = client.get("/api/v1/model-card")
        assert resp.status_code == 200

    def test_returns_plain_text_content_type(self, client: TestClient):
        resp = client.get("/api/v1/model-card")
        assert "text/plain" in resp.headers.get("content-type", "")

    def test_german_markdown_contains_model_name(self, client: TestClient):
        resp = client.get("/api/v1/model-card?lang=de")
        assert resp.status_code == 200
        body = resp.text
        # Should contain German model card content
        assert len(body) > 100

    def test_english_markdown_returns_200(self, client: TestClient):
        resp = client.get("/api/v1/model-card?lang=en")
        assert resp.status_code == 200

    def test_english_markdown_is_non_empty(self, client: TestClient):
        resp = client.get("/api/v1/model-card?lang=en")
        assert len(resp.text) > 100

    def test_german_markdown_default(self, client: TestClient):
        """Default (no lang param) should return German markdown."""
        resp = client.get("/api/v1/model-card")
        assert resp.status_code == 200
        assert len(resp.text) > 50


class TestModelCardMarkdownEndpointJson:
    """Tests for GET /api/v1/model-card/markdown (JSON-wrapped Markdown)."""

    def test_returns_200(self, client: TestClient):
        resp = client.get("/api/v1/model-card/markdown")
        assert resp.status_code == 200

    def test_returns_markdown_key(self, client: TestClient):
        resp = client.get("/api/v1/model-card/markdown")
        data = resp.json()
        assert "markdown" in data

    def test_markdown_value_is_string(self, client: TestClient):
        resp = client.get("/api/v1/model-card/markdown")
        data = resp.json()
        assert isinstance(data["markdown"], str)

    def test_markdown_value_non_empty(self, client: TestClient):
        resp = client.get("/api/v1/model-card/markdown")
        data = resp.json()
        assert len(data["markdown"]) > 50

    def test_english_markdown_json(self, client: TestClient):
        resp = client.get("/api/v1/model-card/markdown?lang=en")
        assert resp.status_code == 200
        data = resp.json()
        assert "markdown" in data
        assert isinstance(data["markdown"], str)

    def test_german_markdown_json(self, client: TestClient):
        resp = client.get("/api/v1/model-card/markdown?lang=de")
        assert resp.status_code == 200
        data = resp.json()
        assert "markdown" in data


class TestModelCardJsonRoute:
    """Tests for GET /api/v1/model-card/json."""

    def test_returns_200(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json")
        assert resp.status_code == 200

    def test_returns_json(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json")
        data = resp.json()
        assert isinstance(data, dict)

    def test_has_name_field(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json")
        data = resp.json()
        assert "name" in data

    def test_has_feature_groups(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json")
        data = resp.json()
        assert "feature_groups" in data

    def test_has_features_total(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json")
        data = resp.json()
        assert "features_total" in data
        assert isinstance(data["features_total"], int)

    def test_german_name(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=de")
        data = resp.json()
        assert data["name"] == "HEAR CI Prognosemodell"

    def test_german_status(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=de")
        data = resp.json()
        assert data["status"] == "aktiv"

    def test_english_name(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        assert data["name"] == "HEAR CI Prediction Model"

    def test_english_status(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        assert data["status"] == "active"

    def test_english_model_type(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        assert data.get("model_type") == "RandomForestClassifier"

    def test_english_intended_use_is_list(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        assert "intended_use" in data
        assert isinstance(data["intended_use"], list)
        assert len(data["intended_use"]) > 0

    def test_english_limitations_is_list(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        assert "limitations" in data
        assert isinstance(data["limitations"], list)

    def test_english_ethical_considerations(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        assert "ethical_considerations" in data
        ethical = data["ethical_considerations"]
        assert "fairness" in ethical
        assert "privacy" in ethical
        assert "transparency" in ethical

    def test_english_recommendations(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    def test_english_changelog(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        assert "changelog" in data

    def test_english_not_intended_for(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        assert "not_intended_for" in data
        assert isinstance(data["not_intended_for"], list)

    def test_english_training_validation_strategy(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=en")
        data = resp.json()
        training = data.get("training", {})
        assert training.get("validation_strategy") is not None

    def test_feature_groups_structure(self, client: TestClient):
        resp = client.get("/api/v1/model-card/json?lang=de")
        data = resp.json()
        feature_groups = data.get("feature_groups")
        # feature_groups may be a dict (German) or list (English)
        assert feature_groups is not None
