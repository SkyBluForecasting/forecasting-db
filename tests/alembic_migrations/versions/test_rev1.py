from alembic import command
from sqlalchemy import inspect

FORECAST_ERRORS_TABLE = {"name": "forecast_errors", "schema": "product"}


# ---------------- Table existence tests ----------------
def test_forecast_errors_table_exists(alembic_cfg, upgraded_engine):
    """Ensure forecast_errors table exists after upgrading to rev1."""
    command.upgrade(alembic_cfg, "rev1")

    inspector = inspect(upgraded_engine)
    tables = inspector.get_table_names(schema=FORECAST_ERRORS_TABLE["schema"])
    assert (
        FORECAST_ERRORS_TABLE["name"] in tables
    ), "forecast_errors table missing in product schema"


def test_forecast_errors_columns(alembic_cfg, upgraded_engine):
    """Check expected columns and their nullability."""
    command.upgrade(alembic_cfg, "rev1")

    inspector = inspect(upgraded_engine)
    columns = {
        c["name"]: c
        for c in inspector.get_columns(
            FORECAST_ERRORS_TABLE["name"], schema=FORECAST_ERRORS_TABLE["schema"]
        )
    }

    expected_columns = {
        "id": {"nullable": False},
        "forecast_run_id": {"nullable": False},
        "timestamp": {"nullable": False},
        "error": {"nullable": False},
    }

    for col_name, props in expected_columns.items():
        assert col_name in columns, f"Missing column {col_name}"
        assert (
            columns[col_name]["nullable"] == props["nullable"]
        ), f"{col_name} nullability mismatch"


def test_forecast_errors_primary_key(alembic_cfg, upgraded_engine):
    """Verify primary key is on id."""
    command.upgrade(alembic_cfg, "rev1")

    inspector = inspect(upgraded_engine)
    pk = inspector.get_pk_constraint(
        FORECAST_ERRORS_TABLE["name"], schema=FORECAST_ERRORS_TABLE["schema"]
    )
    assert pk["constrained_columns"] == ["id"], "Primary key should be on id"


def test_forecast_errors_unique_constraint(alembic_cfg, upgraded_engine):
    """Verify unique constraint on (forecast_run_id, timestamp)."""
    command.upgrade(alembic_cfg, "rev1")

    inspector = inspect(upgraded_engine)
    constraints = inspector.get_unique_constraints(
        FORECAST_ERRORS_TABLE["name"], schema=FORECAST_ERRORS_TABLE["schema"]
    )
    uq_names = [c["name"] for c in constraints]
    assert (
        "uq_forecast_errors_run_ts" in uq_names
    ), "Missing unique constraint uq_forecast_errors_run_ts"


def test_forecast_errors_index_exists(alembic_cfg, upgraded_engine):
    """Verify index on (forecast_run_id, timestamp) exists."""
    command.upgrade(alembic_cfg, "rev1")

    inspector = inspect(upgraded_engine)
    indexes = inspector.get_indexes(
        FORECAST_ERRORS_TABLE["name"], schema=FORECAST_ERRORS_TABLE["schema"]
    )
    index_names = [ix["name"] for ix in indexes]
    assert (
        "ix_forecast_errors_run_ts" in index_names
    ), "Missing index ix_forecast_errors_run_ts"


# ---------------- Upgrade/Downgrade tests ----------------
def test_rev1_upgrade_and_downgrade(alembic_cfg, upgraded_engine):
    """Ensure rev1 upgrade creates and downgrade removes forecast_errors table."""
    # Upgrade to rev1
    command.upgrade(alembic_cfg, "rev1")

    inspector = inspect(upgraded_engine)
    tables = inspector.get_table_names(schema="product")
    assert "forecast_errors" in tables, "forecast_errors missing after upgrade"

    # Downgrade back to rev0
    command.downgrade(alembic_cfg, "rev0")
    inspector = inspect(upgraded_engine)
    tables_after = inspector.get_table_names(schema="product")
    assert (
        "forecast_errors" not in tables_after
    ), "forecast_errors still exists after downgrade"
