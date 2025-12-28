from alembic import command
from sqlalchemy import inspect, text

ASSETS_TABLE = {"name": "assets", "schema": "openstef"}


# ---------------- Columns ----------------
def test_assets_new_columns_exist(alembic_cfg, upgraded_engine):
    command.upgrade(alembic_cfg, "rev2")

    inspector = inspect(upgraded_engine)
    columns = {
        c["name"]: c
        for c in inspector.get_columns(
            ASSETS_TABLE["name"], schema=ASSETS_TABLE["schema"]
        )
    }

    assert "measured" in columns
    assert "depth" in columns

    assert columns["measured"]["nullable"] is False
    assert columns["depth"]["nullable"] is False


def test_assets_column_defaults(alembic_cfg, upgraded_engine):
    command.upgrade(alembic_cfg, "rev2")

    inspector = inspect(upgraded_engine)
    columns = {
        c["name"]: c
        for c in inspector.get_columns(
            ASSETS_TABLE["name"], schema=ASSETS_TABLE["schema"]
        )
    }

    # Server defaults exist (DB-side)
    assert columns["measured"]["default"] is not None
    assert columns["depth"]["default"] is not None


# ---------------- ENUM ----------------
def test_asset_type_enum_exists(alembic_cfg, upgraded_engine):
    command.upgrade(alembic_cfg, "rev2")

    with upgraded_engine.connect() as conn:
        enum_exists = conn.execute(
            text(
                """
                SELECT 1
                FROM pg_type
                WHERE typname = 'asset_type_enum'
                """
            )
        ).fetchone()

    assert enum_exists is not None


def test_asset_type_column_uses_enum(alembic_cfg, upgraded_engine):
    command.upgrade(alembic_cfg, "rev2")

    inspector = inspect(upgraded_engine)
    cols = inspector.get_columns(ASSETS_TABLE["name"], schema=ASSETS_TABLE["schema"])

    asset_type = next(c for c in cols if c["name"] == "asset_type")

    assert asset_type["nullable"] is False
    assert asset_type["type"].__class__.__name__ == "ENUM"


# ---------------- Data migration ----------------
def test_substation_mapped_to_distribution_substation(alembic_cfg, upgraded_engine):
    command.upgrade(alembic_cfg, "rev1")

    with upgraded_engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO openstef.assets (
                    asset_uuid,
                    name,
                    asset_type
                )
                VALUES (
                    'TEST_SUB_1',
                    'Test Substation',
                    'substation'
                )
                """
            )
        )

    command.upgrade(alembic_cfg, "rev2")

    with upgraded_engine.connect() as conn:
        count = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM openstef.assets
                WHERE asset_uuid = 'TEST_SUB_1'
                  AND asset_type = 'distribution_substation'
                """
            )
        ).scalar()

    assert count == 1


def test_existing_assets_get_defaults(alembic_cfg, upgraded_engine):
    command.upgrade(alembic_cfg, "rev1")

    with upgraded_engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO openstef.assets (
                    asset_uuid,
                    name,
                    asset_type
                )
                VALUES (
                    'TEST_SYS_1',
                    'Test System',
                    'system'
                )
                """
            )
        )

    command.upgrade(alembic_cfg, "rev2")

    with upgraded_engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT measured, depth
                FROM openstef.assets
                WHERE asset_uuid = 'TEST_SYS_1'
                """
            )
        ).fetchone()

    assert row.measured is False
    assert row.depth == 0


# ---------------- Upgrade / Downgrade ----------------
def test_rev2_upgrade_and_downgrade(alembic_cfg, upgraded_engine):
    command.upgrade(alembic_cfg, "rev2")

    inspector = inspect(upgraded_engine)
    col_names = [
        c["name"]
        for c in inspector.get_columns(
            ASSETS_TABLE["name"], schema=ASSETS_TABLE["schema"]
        )
    ]

    assert "measured" in col_names
    assert "depth" in col_names

    # Downgrade back to rev1
    command.downgrade(alembic_cfg, "rev1")

    inspector = inspect(upgraded_engine)
    col_names_after = [
        c["name"]
        for c in inspector.get_columns(
            ASSETS_TABLE["name"], schema=ASSETS_TABLE["schema"]
        )
    ]

    assert "measured" not in col_names_after
    assert "depth" not in col_names_after
