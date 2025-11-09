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
    # Create schemas if missing
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS openstef;"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS product;"))

    # Upgrade Alembic using the same connection
    conn = engine.connect()
    alembic_cfg.attributes["connection"] = conn
    command.upgrade(alembic_cfg, "rev0")

    yield engine

    # Downgrade back to base after test
    command.downgrade(alembic_cfg, "base")
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
