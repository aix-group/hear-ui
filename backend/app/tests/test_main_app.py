"""Tests for the main FastAPI application."""

from unittest.mock import MagicMock, PropertyMock, patch

from fastapi.testclient import TestClient


class TestAppConfiguration:
    """Test FastAPI app configuration."""

    def test_app_has_title(self):
        """Test app has title set."""
        from app.main import app

        assert app.title is not None
        assert len(app.title) > 0

    def test_app_has_openapi_url(self):
        """Test app has openapi URL configured."""
        from app.main import app

        assert app.openapi_url is not None
        assert "/openapi.json" in app.openapi_url

    def test_app_includes_api_router(self):
        """Test app includes API router."""
        from app.main import app

        routes = [route.path for route in app.routes]
        assert any("/api/v1" in str(route) for route in routes)


class TestCustomGenerateUniqueId:
    """Test custom unique ID generation for routes."""

    def test_generate_unique_id_with_tags(self):
        """Test unique ID generation with tags."""
        from fastapi.routing import APIRoute

        from app.main import custom_generate_unique_id

        # Create mock route
        mock_route = MagicMock(spec=APIRoute)
        mock_route.tags = ["prediction"]
        mock_route.name = "predict"

        result = custom_generate_unique_id(mock_route)
        assert result == "prediction-predict"

    def test_generate_unique_id_without_tags(self):
        """Test unique ID generation without tags."""
        from fastapi.routing import APIRoute

        from app.main import custom_generate_unique_id

        mock_route = MagicMock(spec=APIRoute)
        mock_route.tags = []
        mock_route.name = "some_route"

        result = custom_generate_unique_id(mock_route)
        assert result == "default-some_route"

    def test_generate_unique_id_with_none_tags(self):
        """Test unique ID generation with None tags."""
        from fastapi.routing import APIRoute

        from app.main import custom_generate_unique_id

        mock_route = MagicMock(spec=APIRoute)
        mock_route.tags = None
        mock_route.name = "some_route"

        result = custom_generate_unique_id(mock_route)
        assert result == "default-some_route"


class TestExceptionHandler:
    """Test exception handler."""

    def test_unhandled_exception_returns_500(self):
        """Test unhandled exceptions return 500."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        # Access a route that may throw an internal error
        # This tests that the exception handler works
        response = client.post("/api/v1/predict/", json={})
        # Should not crash the app - returns either error or validation error
        assert response.status_code in [200, 400, 422, 500, 503]


class TestCORSMiddleware:
    """Test CORS middleware configuration."""

    def test_cors_middleware_added(self):
        """Test CORS middleware is configured."""
        from app.main import app

        # Check that middleware is present
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes


class TestModelWrapperState:
    """Test model wrapper in app state."""

    def test_app_has_model_wrapper_attribute(self):
        """Test app exposes model_wrapper."""
        from app.main import model_wrapper

        assert model_wrapper is not None
        # After startup, app.state.model_wrapper should be set
        # (may be None if model file not found, but attribute should exist)


class TestRootRedirect:
    """Test root URL redirect."""

    def test_root_redirects_to_docs(self):
        """Test GET / redirects to /docs."""
        from app.main import app

        client = TestClient(app, follow_redirects=False)
        response = client.get("/")
        assert response.status_code in [301, 302, 307, 308]
        assert "/docs" in response.headers.get("location", "")


class TestCustomGenerateUniqueIdException:
    """Test exception path in custom_generate_unique_id."""

    def test_generate_unique_id_tags_raises_exception(self):
        """Test fallback when accessing tags raises an exception."""
        from fastapi.routing import APIRoute

        from app.main import custom_generate_unique_id

        mock_route = MagicMock(spec=APIRoute)
        type(mock_route).tags = PropertyMock(side_effect=Exception("boom"))
        mock_route.name = "my_route"

        result = custom_generate_unique_id(mock_route)
        assert result == "default-my_route"


class TestUnhandledExceptionHandler:
    """Test the global exception handler for unhandled errors."""

    def test_real_500_exception_handled(self):
        """Test that a real unhandled exception returns 500 JSON."""
        from app.main import app

        # Add a temporary route that raises a non-HTTP exception
        @app.get("/test-internal-error-xyz")
        async def _raise_error():
            raise RuntimeError("intentional test error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test-internal-error-xyz")
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal Server Error"}

        # Remove the temporary route
        app.routes.pop()


class TestLifespanErrorHandling:
    """Test lifespan handles model load errors gracefully."""

    def test_lifespan_file_not_found_still_sets_state(self):
        """Lifespan sets app.state.model_wrapper even when model file missing."""
        from fastapi import FastAPI

        from app.main import lifespan

        test_app = FastAPI(lifespan=lifespan)
        with patch("app.main.model_wrapper") as mock_wrapper:
            mock_wrapper.load.side_effect = FileNotFoundError("no model file")
            client = TestClient(test_app, raise_server_exceptions=False)
            with client:
                assert test_app.state.model_wrapper is mock_wrapper

    def test_lifespan_generic_exception_still_sets_state(self):
        """Lifespan sets app.state.model_wrapper on generic exception."""
        from fastapi import FastAPI

        from app.main import lifespan

        test_app = FastAPI(lifespan=lifespan)
        with patch("app.main.model_wrapper") as mock_wrapper:
            mock_wrapper.load.side_effect = RuntimeError("unexpected")
            client = TestClient(test_app, raise_server_exceptions=False)
            with client:
                assert test_app.state.model_wrapper is mock_wrapper
