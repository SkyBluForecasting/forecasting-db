import pytest
from alembic import command
from sqlalchemy import inspect

# ---------------- Table definitions ----------------
TABLES = [
    {"name": "assets", "schema": "openstef"},
    {"name": "prediction_job", "schema": "openstef"},
    {"name": "forecast_runs", "schema": "openstef"},
    {"name": "forecast", "schema": "openstef"},
    {"name": "measurement", "schema": "openstef"},
    {"name": "constraints", "schema": "product"},
]


# ---------------- Tests ----------------
@pytest.mark.parametrize("table", TABLES)
def test_table_exists_and_columns(upgraded_engine, table):
    """Verify each table exists and has at least one column."""
    inspector = inspect(upgraded_engine)
    table_names = inspector.get_table_names(schema=table["schema"])
    assert table["name"] in table_names, f"{table['name']} missing in {table['schema']}"

    columns = inspector.get_columns(table["name"], schema=table["schema"])
    assert len(columns) > 0, f"{table['name']} has no columns"


@pytest.mark.parametrize("table", TABLES)
def test_table_primary_keys(upgraded_engine, table):
    """Verify each table has a primary key."""
    inspector = inspect(upgraded_engine)
    pk = inspector.get_pk_constraint(table["name"], schema=table["schema"])
    assert pk["constrained_columns"], f"{table['name']} has no primary key"


@pytest.mark.parametrize("table", TABLES)
def test_table_indexes(upgraded_engine, table):
    """Verify indexes exist (at least the call should succeed)."""
    inspector = inspect(upgraded_engine)
    indexes = inspector.get_indexes(table["name"], schema=table["schema"])
    assert isinstance(indexes, list)


# ---------------- Specific column/constraint tests ----------------
def test_measurement_unique_constraint(upgraded_engine):
    """Verify measurement table has unique constraint on (asset_uuid, timestamp, metric)."""
    inspector = inspect(upgraded_engine)
    constraints = inspector.get_unique_constraints("measurement", schema="openstef")
    uq_names = [c["name"] for c in constraints]
    assert "uq_measurement_asset_ts_metric" in uq_names


def test_measurement_columns_not_nullable(upgraded_engine):
    """Verify important measurement columns are non-nullable."""
    inspector = inspect(upgraded_engine)
    columns = {
        c["name"]: c for c in inspector.get_columns("measurement", schema="openstef")
    }
    for col in ["asset_uuid", "timestamp", "metric", "value"]:
        assert col in columns
        assert not columns[col]["nullable"]


# ---------------- Upgrade/downgrade tests ----------------
@pytest.mark.parametrize("table", TABLES)
def test_downgrade_removes_tables(alembic_cfg, upgraded_engine, table):
    """Verify that downgrade removes the tables."""
    # Upgrade first
    command.upgrade(alembic_cfg, "rev0")
    inspector = inspect(upgraded_engine)
    table_names = inspector.get_table_names(schema=table["schema"])
    assert table["name"] in table_names, f"{table['name']} missing after upgrade"

    # Downgrade
    command.downgrade(alembic_cfg, "base")
    inspector = inspect(upgraded_engine)
    table_names_after = inspector.get_table_names(schema=table["schema"])
    assert (
        table["name"] not in table_names_after
    ), f"{table['name']} still exists after downgrade"
