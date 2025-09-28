import pytest
from sqlalchemy import inspect


@pytest.mark.parametrize("alembic_migrate_to_revision", ["rev0"], indirect=True)
def test_forecasts_table_created(alembic_migrate_to_revision):
    inspector = inspect(alembic_migrate_to_revision)
    tables = inspector.get_table_names()
    assert "forecasts" in tables

    # check columns
    cols = {c["name"]: c for c in inspector.get_columns("forecasts")}
    assert "asset_uuid" in cols
    assert cols["asset_uuid"]["type"].__class__.__name__ == "VARCHAR"
    assert "timestamp" in cols
    assert cols["timestamp"]["type"].__class__.__name__ == "TIMESTAMP"
    assert "forecast_kw" in cols
    assert cols["forecast_kw"]["type"].__class__.__name__ == "DOUBLE_PRECISION"
    assert "forecast_uuid" in cols
    assert cols["forecast_uuid"]["type"].__class__.__name__ == "UUID"

    # check primary key columns
    pk_cols = inspector.get_pk_constraint("forecasts")["constrained_columns"]
    assert set(pk_cols) == {"asset_uuid", "timestamp", "forecast_uuid"}

    # check index
    indexes = inspector.get_indexes("forecasts")
    index_names = [idx["name"] for idx in indexes]
    assert "ix_forecasts_forecast_uuid" in index_names


def test_downgrade_drops_forecasts_table(alembic_cfg, engine):
    """Test that downgrade removes the forecasts table."""
    from alembic import command

    # run upgrade first
    command.upgrade(alembic_cfg, "rev0")
    inspector = inspect(engine)
    assert "forecasts" in inspector.get_table_names()

    # run downgrade
    command.downgrade(alembic_cfg, "base")
    inspector = inspect(engine)
    assert "forecasts" not in inspector.get_table_names()
