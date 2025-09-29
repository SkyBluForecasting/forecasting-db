import pytest
from sqlalchemy import inspect

TABLES = [
    {
        "name": "forecasts",
        "pk": {"asset_uuid", "timestamp", "forecast_uuid"},
        "columns": {
            "asset_uuid": "VARCHAR",
            "timestamp": "TIMESTAMP",
            "forecast_kw": "DOUBLE_PRECISION",
            "forecast_uuid": "UUID",
        },
        "indexes": ["ix_forecasts_forecast_uuid"],
    },
    {
        "name": "forecast_runs",
        "pk": {"forecast_uuid"},
        "columns": {
            "forecast_uuid": "UUID",
            "run_uuid": "VARCHAR",
            "asset_uuid": "VARCHAR",
            "created_at": "TIMESTAMP",
            "start_time": "TIMESTAMP",
            "end_time": "TIMESTAMP",
            "frequency_min": "DOUBLE_PRECISION",
        },
        "indexes": ["ix_forecast_runs_asset_uuid"],
    },
    {
        "name": "constraints",
        "pk": {"asset_uuid", "timestamp", "forecast_uuid"},
        "columns": {
            "asset_uuid": "VARCHAR",
            "timestamp": "TIMESTAMP",
            "forecast_uuid": "UUID",
            "constraint_kw": "DOUBLE_PRECISION",
        },
        "indexes": ["ix_constraints_forecast_uuid"],
    },
    {
        "name": "measurements",
        "pk": {"asset_uuid", "timestamp", "metric"},
        "columns": {
            "asset_uuid": "VARCHAR",
            "timestamp": "TIMESTAMP",
            "metric": "VARCHAR",
            "value": "DOUBLE_PRECISION",
        },
        "indexes": [],
    },
]


@pytest.mark.parametrize("table", TABLES)
def test_table_columns(alembic_migrate_to_revision, table):
    inspector = inspect(alembic_migrate_to_revision)
    assert table["name"] in inspector.get_table_names()
    cols = {c["name"]: c for c in inspector.get_columns(table["name"])}
    for col_name, col_type in table["columns"].items():
        assert col_name in cols
        assert cols[col_name]["type"].__class__.__name__.upper() == col_type


@pytest.mark.parametrize("table", TABLES)
def test_table_primary_keys(alembic_migrate_to_revision, table):
    inspector = inspect(alembic_migrate_to_revision)
    pk = inspector.get_pk_constraint(table["name"])["constrained_columns"]
    assert set(pk) == table["pk"]


@pytest.mark.parametrize("table", TABLES)
def test_table_indexes(alembic_migrate_to_revision, table):
    inspector = inspect(alembic_migrate_to_revision)
    existing_indexes = [idx["name"] for idx in inspector.get_indexes(table["name"])]
    for idx_name in table["indexes"]:
        assert idx_name in existing_indexes


@pytest.mark.parametrize(
    "table_name", ["forecasts", "forecast_runs", "constraints", "measurements"]
)
def test_downgrade_drops_tables(alembic_cfg, engine, table_name):
    """Test that downgrade removes the tables."""
    from alembic import command

    # run upgrade first
    command.upgrade(alembic_cfg, "rev0")
    inspector = inspect(engine)
    assert table_name in inspector.get_table_names()

    # run downgrade
    command.downgrade(alembic_cfg, "base")
    inspector = inspect(engine)
    assert table_name not in inspector.get_table_names()
