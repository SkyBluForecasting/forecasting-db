import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

# Use a dedicated test database, e.g. "postgres://user:pass@localhost:5432/test_db"
TEST_DB_URL = "postgresql://postgres:localpass@localhost:5432/appdb"


@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine for the test database."""
    engine = create_engine(TEST_DB_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def connection(engine):
    """Provide a connection and rollback after each test session."""
    connection = engine.connect()
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def alembic_cfg():
    """Configure Alembic for the test database."""
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    return cfg


@pytest.fixture
def alembic_migrate_to_revision(alembic_cfg, connection, request):
    """
    Run Alembic migrations up to a specific revision for a test.

    Usage:
        @pytest.mark.parametrize("revision", ["rev0", "rev1"])
        def test_something(alembic_migrate_to_revision):
            ...
    """
    revision = getattr(request, "param", "head")  # default to head if not specified
    trans = connection.begin()
    alembic_cfg.attributes["connection"] = connection
    command.upgrade(alembic_cfg, revision)

    yield connection

    trans.rollback()
