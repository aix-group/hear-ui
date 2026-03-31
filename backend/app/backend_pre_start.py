import logging
import sys
import time

from sqlmodel import Session, create_engine, select

from app.core.config import settings

logger = logging.getLogger(__name__)


def init(engine: object | None = None) -> None:
    """Attempt to use SQLModel Session to execute a simple query.

    This function is exercised by unit tests (they call init(engine_mock)).
    When called without an engine, we construct one from settings.SQLALCHEMY_DATABASE_URI.
    """
    if engine is None:
        try:
            engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        except Exception as e:
            logger.error("Failed to create engine: %s", e)
            raise

    # Try to open a session and run a lightweight statement to validate connectivity
    try:
        with Session(engine) as session:
            # Execute a trivial statement - using SQLModel/SQLAlchemy layer
            session.exec(select(1))
            logger.info("Database connection check succeeded.")
    except Exception as e:
        logger.error("Database connection check failed: %s", e)
        raise


if __name__ == "__main__":
    # CLI entrypoint used by scripts/prestart.sh
    logging.basicConfig(level=logging.INFO)

    max_retries = 10
    delay_seconds = 3

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            init()
            logger.info("DB_READY")
            sys.exit(0)
        except Exception as e:
            last_exc = e
            logger.warning("DB not ready (attempt %d/%d): %s", attempt, max_retries, e)
            time.sleep(delay_seconds)

    logger.error("DB did not become ready after %d attempts: %s", max_retries, last_exc)
    sys.exit(1)
