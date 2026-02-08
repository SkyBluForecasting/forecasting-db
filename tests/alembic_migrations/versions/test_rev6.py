import sqlalchemy as sa
from alembic import command
from sqlalchemy import inspect

SCHEMA_OPENSTEF = "openstef"
SCHEMA_PUBLIC = "public"


def column_info(engine, schema, table, column):
    inspector = inspect(engine)
    cols = inspector.get_columns(table, schema=schema)
    for col in cols:
        if col["name"] == column:
            return col
    return None


def enum_labels(engine, schema, enum_name):
    """Return ordered labels for a Postgres enum type, e.g. public.asset_type_enum."""
    sql = sa.text(
        """
        SELECT e.enumlabel
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = :schema
          AND t.typname = :enum_name
        ORDER BY e.enumsortorder
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql, {"schema": schema, "enum_name": enum_name}).fetchall()
    return [r[0] for r in rows]


def test_rev6_columns_and_enum_on_upgrade(alembic_cfg, upgraded_engine):
    """
    Upgrade to rev6.

      - openstef.assets has latitude, longitude, weather_site_id (all nullable)
      - public.asset_type_enum includes 'pv'
    """
    command.upgrade(alembic_cfg, "rev6")

    # --- assets columns ---
    lat = column_info(upgraded_engine, SCHEMA_OPENSTEF, "assets", "latitude")
    lon = column_info(upgraded_engine, SCHEMA_OPENSTEF, "assets", "longitude")
    wsi = column_info(upgraded_engine, SCHEMA_OPENSTEF, "assets", "weather_site_id")

    assert lat is not None
    assert lon is not None
    assert wsi is not None

    assert lat["nullable"] is True
    assert lon["nullable"] is True
    assert wsi["nullable"] is True

    # Optional: type checks (keep them a bit loose to avoid dialect quirks)
    assert isinstance(lat["type"], sa.types.Float)
    assert isinstance(lon["type"], sa.types.Float)
    assert isinstance(wsi["type"], sa.types.String)

    # --- enum includes pv ---
    labels = enum_labels(upgraded_engine, SCHEMA_PUBLIC, "asset_type_enum")
    assert "pv" in labels


def test_rev6_columns_removed_on_downgrade(alembic_cfg, upgraded_engine):
    """
    Downgrade from rev6 -> rev5.

      - columns are removed from openstef.assets
      - enum value 'pv' is NOT expected to be removed (Postgres limitation)
    """
    command.upgrade(alembic_cfg, "rev6")
    command.downgrade(alembic_cfg, "rev5")

    # columns should be gone
    assert column_info(upgraded_engine, SCHEMA_OPENSTEF, "assets", "latitude") is None
    assert column_info(upgraded_engine, SCHEMA_OPENSTEF, "assets", "longitude") is None
    assert (
        column_info(upgraded_engine, SCHEMA_OPENSTEF, "assets", "weather_site_id")
        is None
    )

    # NOTE: do not assert 'pv' removed from enum; Postgres doesn't support easy removal.
    labels = enum_labels(upgraded_engine, SCHEMA_PUBLIC, "asset_type_enum")
    assert "pv" in labels
