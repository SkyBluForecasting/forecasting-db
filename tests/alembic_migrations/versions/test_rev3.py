# tests/alembic/test_rev3.py
from alembic import command
from sqlalchemy import String, inspect

ASSETS_TABLE = {"name": "assets", "schema": "openstef"}


# ---------------- Columns ----------------
def test_assets_columns_have_no_length_limit(alembic_cfg, upgraded_engine):
    # Upgrade to rev2 first (baseline)
    command.upgrade(alembic_cfg, "rev2")
    # Apply rev3
    command.upgrade(alembic_cfg, "rev3")

    inspector = inspect(upgraded_engine)
    columns = {
        c["name"]: c
        for c in inspector.get_columns(
            ASSETS_TABLE["name"], schema=ASSETS_TABLE["schema"]
        )
    }

    for col_name in ("asset_uuid", "name", "parent_uuid"):
        col_type = columns[col_name]["type"]
        # Column should be a String type
        assert isinstance(col_type, String)
        # No length limit after rev3
        assert col_type.length is None


def test_assets_columns_length_restored_on_downgrade(alembic_cfg, upgraded_engine):
    # Upgrade to rev3 first
    command.upgrade(alembic_cfg, "rev3")
    # Downgrade back to rev2
    command.downgrade(alembic_cfg, "rev2")

    inspector = inspect(upgraded_engine)
    columns = {
        c["name"]: c
        for c in inspector.get_columns(
            ASSETS_TABLE["name"], schema=ASSETS_TABLE["schema"]
        )
    }

    # Check the original length limits restored
    assert columns["asset_uuid"]["type"].length == 50
    assert columns["name"]["type"].length == 100
    assert columns["parent_uuid"]["type"].length == 50
