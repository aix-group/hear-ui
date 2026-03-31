"""
Test fixtures with Testcontainers for isolated PostgreSQL testing.

This module provides:
- Isolated PostgreSQL container for each test session
- Automatic database cleanup between tests
- Fallback to existing database if Docker is unavailable
"""

import os
import warnings
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, text

# ============================================================================
# Shared test helpers
# ============================================================================


def get_valid_predict_payload() -> dict:
    """Return minimal valid patient data that passes predict endpoint validation.

    Includes the 4 critical fields plus one extra to meet the 5-field minimum.
    Use this for any test that POSTs to /api/v1/predict/.
    """
    return {
        "Alter [J]": 50.0,
        "Geschlecht": "m",
        "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
        "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
        "Primäre Sprache": "Deutsch",
    }


# Check if testcontainers is available and enabled
testcontainers_disabled = (
    os.getenv("TESTCONTAINERS_DISABLED", "false").lower() == "true"
)

try:
    from testcontainers.postgres import PostgresContainer

    TESTCONTAINERS_AVAILABLE = not testcontainers_disabled
except ImportError:
    TESTCONTAINERS_AVAILABLE = False
    # If the user hasn't opted into using an existing DB, fail fast with clear instructions.
    use_existing = os.getenv("USE_EXISTING_DB", "false").lower() == "true"
    if not use_existing:
        raise RuntimeError(
            "testcontainers is not installed in the test environment and `USE_EXISTING_DB` is not set. "
            'Install it with `pip install "testcontainers[postgres]"` and ensure Docker is running, '
            "or set the environment variable `USE_EXISTING_DB=true` to point tests to an existing PostgreSQL instance."
        )
    else:
        warnings.warn(
            "testcontainers not installed. Using existing database for tests because USE_EXISTING_DB=true.",
            stacklevel=2,
        )


def _create_test_engine(database_url: str):
    """Create a test database engine."""
    return create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )


def _init_test_db(engine):
    """Initialize test database tables."""
    SQLModel.metadata.create_all(engine)


# Global container reference (kept alive for session scope)
_postgres_container = None
_test_engine = None


@pytest.fixture(scope="session")
def postgres_container():
    """
    Create a PostgreSQL container for the test session.

    Falls back to existing database if:
    - testcontainers is not installed
    - Docker is not available
    - USE_EXISTING_DB=true environment variable is set
    """
    global _postgres_container, _test_engine

    use_existing_db = os.getenv("USE_EXISTING_DB", "false").lower() == "true"

    if use_existing_db or not TESTCONTAINERS_AVAILABLE:
        # Use existing database
        from app.core.config import settings

        database_url = str(settings.SQLALCHEMY_DATABASE_URI)
        _test_engine = _create_test_engine(database_url)
        yield {"url": database_url, "engine": _test_engine, "container": None}
        return

    try:
        # Start PostgreSQL container
        _postgres_container = PostgresContainer(
            image="postgres:15-alpine",
            username="test",
            password="test",
            dbname="testdb",
        )
        _postgres_container.start()

        # Get connection URL
        database_url = _postgres_container.get_connection_url()
        _test_engine = _create_test_engine(database_url)

        # Initialize tables
        _init_test_db(_test_engine)

        yield {
            "url": database_url,
            "engine": _test_engine,
            "container": _postgres_container,
        }

    except Exception as e:
        warnings.warn(
            f"Could not start Postgres container: {e}. Using existing database.",
            stacklevel=2,
        )
        from app.core.config import settings

        database_url = str(settings.SQLALCHEMY_DATABASE_URI)
        _test_engine = _create_test_engine(database_url)
        yield {"url": database_url, "engine": _test_engine, "container": None}

    finally:
        if _postgres_container is not None:
            try:
                _postgres_container.stop()
            except Exception:
                pass


@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """Get the database engine (from container or existing DB)."""
    return postgres_container["engine"]


@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    """
    Database session fixture with automatic cleanup.

    Each test gets a fresh session and changes are rolled back after the test.
    """
    # Import models to ensure they're registered
    from app.models import Feedback, Patient, Prediction  # noqa: F401

    # Create tables if they don't exist
    SQLModel.metadata.create_all(db_engine)

    with Session(db_engine) as session:
        yield session
        # Rollback any uncommitted changes
        session.rollback()


@pytest.fixture(scope="function")
def clean_db(db: Session) -> Generator[Session, None, None]:
    """
    Database session with guaranteed clean state.

    Deletes all data from tables before the test runs.
    Use this for tests that need a completely empty database.
    """
    # Clean all tables
    tables = ["feedback", "prediction", "patient"]
    for table in tables:
        try:
            db.exec(text(f"DELETE FROM {table}"))
        except Exception:
            pass  # Table might not exist
    db.commit()

    yield db


@pytest.fixture(scope="module")
def client(postgres_container) -> Generator[TestClient, None, None]:
    """
    Test client with proper database configuration.

    Overrides the database URL to use the test container.
    """
    # Override database URL in settings
    database_url = postgres_container["url"]

    # Patch settings before importing app
    original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url

    try:
        from app.main import app

        with TestClient(app) as c:
            yield c
    finally:
        # Restore original settings
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    """Authentication fixture (skipped - auth removed)."""
    pytest.skip("auth fixtures removed")


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Authentication fixture (skipped - auth removed)."""
    pytest.skip("auth fixtures removed")


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_patient_data() -> dict:
    """Sample patient data for testing predictions and CRUD operations.

    This is the single authoritative test fixture for patient data.
    Includes enough fields for both predict validation and patient CRUD tests.
    """
    return {
        "Alter [J]": 45,
        "Geschlecht": "w",
        "Seiten": "L",
        "Primäre Sprache": "Deutsch",
        "Diagnose.Höranamnese.Hörminderung operiertes Ohr...": "Hochgradiger HV",
        "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
        "Diagnose.Höranamnese.Ursache....Ursache...": "Unbekannt",
        "Diagnose.Höranamnese.Versorgung Gegenohr...": "Hörgerät",
        "Symptome präoperativ.Tinnitus...": "ja",
        "Behandlung/OP.CI Implantation": "Behandlung/OP.CI Implantation.Cochlear... Nucleus Profile CI532 (Slim Modiolar)",
        "outcome_measurments.pre.measure.": 10,
        "abstand": 365,
    }


@pytest.fixture
def minimal_patient_data() -> dict:
    """Minimal patient data for testing."""
    return {
        "age": 45,
        "gender": "m",
    }


@pytest.fixture
def test_patient(db: Session):
    """Create a test patient in the database for testing."""
    from app import crud
    from app.models import PatientCreate

    patient_in = PatientCreate(
        input_features={
            "Alter [J]": 45,
            "Geschlecht": "w",
            "Primäre Sprache": "Deutsch",
            "Diagnose.Höranamnese.Beginn der Hörminderung (OP-Ohr)...": "postlingual",
        },
        display_name="Test Patient Fixture",
    )
    patient = crud.create_patient(session=db, patient_in=patient_in)
    db.commit()
    db.refresh(patient)
    return patient
