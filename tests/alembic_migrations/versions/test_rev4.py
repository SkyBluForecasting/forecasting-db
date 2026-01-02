from alembic import command
from sqlalchemy import text

SCHEMA_NAME = "mlflow"


def schema_exists(engine, schema_name):
    """Check if a schema exists in Postgres."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name=:schema"
            ),
            {"schema": schema_name},
        )
        return result.first() is not None


def test_mlflow_schema_created_on_upgrade(alembic_cfg, upgraded_engine):
    # Upgrade to rev4
    command.upgrade(alembic_cfg, "rev4")

    # Check that the mlflow schema now exists
    assert schema_exists(upgraded_engine, SCHEMA_NAME)


def test_mlflow_schema_removed_on_downgrade(alembic_cfg, upgraded_engine):
    # Upgrade to rev4 first
    command.upgrade(alembic_cfg, "rev4")
    # Downgrade back to rev3
    command.downgrade(alembic_cfg, "rev3")

    # Schema should no longer exist
    assert not schema_exists(upgraded_engine, SCHEMA_NAME)
