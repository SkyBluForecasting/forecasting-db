import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from forecasting_db.models import Base

TEST_DB_URL = "postgresql://postgres:localpass@localhost:5432/appdb"


@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine for the test database."""
    engine = create_engine(TEST_DB_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def alembic_cfg():
    """Configure Alembic for the test database."""
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    return cfg


@pytest.fixture(scope="function")
def upgraded_engine(alembic_cfg, engine):
    """
    Provide an engine with Alembic upgraded to rev0 for the duration of the test.

    Uses the same connection for Alembic migrations and schema setup.
    """
    # Clean up database state before test
    with engine.begin() as conn:
        # Drop existing schemas to ensure clean state
        conn.execute(text("DROP SCHEMA IF EXISTS product CASCADE;"))
        conn.execute(text("DROP SCHEMA IF EXISTS openstef CASCADE;"))
        # Reset alembic_version table
        conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))
        # Recreate schemas
        conn.execute(text("CREATE SCHEMA openstef;"))
        conn.execute(text("CREATE SCHEMA product;"))

    # Upgrade Alembic using the same connection
    conn = engine.connect()
    alembic_cfg.attributes["connection"] = conn
    command.upgrade(alembic_cfg, "rev0")

    yield engine

    # Clean up after test
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS product CASCADE;"))
        conn.execute(text("DROP SCHEMA IF EXISTS openstef CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))
    conn.close()


@pytest.fixture
def session(engine):
    """Provide a fresh SQLAlchemy session with tables created from models."""
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS openstef"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS product"))

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.rollback()
    s.close()
    Base.metadata.drop_all(engine)
