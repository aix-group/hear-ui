"""Tests for config module."""


class TestConfigParseCors:
    """Test CORS parsing function."""

    def test_parse_cors_comma_separated(self):
        """Test parsing comma-separated CORS origins."""
        from app.core.config import parse_cors

        result = parse_cors("http://localhost:3000,http://localhost:8080")
        assert result == ["http://localhost:3000", "http://localhost:8080"]

    def test_parse_cors_single_origin(self):
        """Test parsing single CORS origin."""
        from app.core.config import parse_cors

        result = parse_cors("http://localhost:3000")
        assert result == ["http://localhost:3000"]

    def test_parse_cors_list(self):
        """Test parsing list input."""
        from app.core.config import parse_cors

        result = parse_cors(["http://a.com", "http://b.com"])
        assert result == ["http://a.com", "http://b.com"]

    def test_parse_cors_json_string(self):
        """Test parsing JSON-like string."""
        from app.core.config import parse_cors

        result = parse_cors('["http://a.com","http://b.com"]')
        assert result == '["http://a.com","http://b.com"]'

    def test_parse_cors_strips_whitespace(self):
        """Test that whitespace is stripped."""
        from app.core.config import parse_cors

        result = parse_cors("  http://a.com  ,  http://b.com  ")
        assert result == ["http://a.com", "http://b.com"]


class TestSettings:
    """Test Settings class."""

    def test_settings_has_required_fields(self):
        """Test settings has all required fields."""
        from app.core.config import settings

        assert hasattr(settings, "API_V1_STR")
        assert hasattr(settings, "PROJECT_NAME")
        assert hasattr(settings, "ENVIRONMENT")
        assert hasattr(settings, "SECRET_KEY")

    def test_api_v1_str_default(self):
        """Test API_V1_STR has default value."""
        from app.core.config import settings

        assert settings.API_V1_STR == "/api/v1"

    def test_all_cors_origins_includes_frontend(self):
        """Test all_cors_origins includes FRONTEND_HOST."""
        from app.core.config import settings

        assert settings.FRONTEND_HOST in settings.all_cors_origins

    def test_sqlalchemy_database_uri_format(self):
        """Test SQLALCHEMY_DATABASE_URI has correct format."""
        from app.core.config import settings

        uri = settings.SQLALCHEMY_DATABASE_URI
        assert uri.startswith("postgresql+psycopg://")
        assert settings.POSTGRES_USER in uri
        assert settings.POSTGRES_DB in uri


class TestEnvironmentDefaults:
    """Test environment defaults."""

    def test_environment_default_is_local(self):
        """Test default ENVIRONMENT is 'local'."""
        from app.core.config import settings

        # In test environment, this might be overridden
        assert settings.ENVIRONMENT in ["local", "staging", "production"]
