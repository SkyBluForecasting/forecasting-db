import pytest
from alembic import command
from sqlalchemy import inspect

# ---------------- Table definitions ----------------
TABLES = [
    {"name": "assets", "schema": "openstef"},
    {"name": "prediction_job", "schema": "openstef"},
    {"name": "forecast_runs", "schema": "openstef"},  # added
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
