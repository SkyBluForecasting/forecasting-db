import sqlalchemy as sa
from alembic import command
from sqlalchemy import inspect

SCHEMA_OPENSTEF = "openstef"
SCHEMA_PRODUCT = "product"


def column_info(engine, schema, table, column):
    inspector = inspect(engine)
    cols = inspector.get_columns(table, schema=schema)
    for col in cols:
        if col["name"] == column:
            return col
    return None


def table_exists(engine, schema, table):
    inspector = inspect(engine)
    return table in inspector.get_table_names(schema=schema)


def index_names(engine, schema, table):
    inspector = inspect(engine)
    idx = inspector.get_indexes(table, schema=schema)
    return {i["name"] for i in idx}


def fk_constraints(engine, schema, table):
    inspector = inspect(engine)
    return inspector.get_foreign_keys(table, schema=schema)


def test_rev7_weather_sites_and_fk_on_upgrade(alembic_cfg, upgraded_engine):
    """
    Upgrade to rev7.

      - product.weather_sites exists with required columns
      - uq_weather_sites_lat_long exists (unique constraint)
      - ix_weather_sites_lat_long exists (index)
      - openstef.assets has index on weather_site_id
      - openstef.assets.weather_site_id has FK -> product.weather_sites.weather_site_id
    """
    command.upgrade(alembic_cfg, "rev7")

    # --- table exists ---
    assert table_exists(upgraded_engine, SCHEMA_PRODUCT, "weather_sites") is True

    # --- columns exist + types/nullability ---
    wsi = column_info(
        upgraded_engine, SCHEMA_PRODUCT, "weather_sites", "weather_site_id"
    )
    lat = column_info(upgraded_engine, SCHEMA_PRODUCT, "weather_sites", "site_lat")
    lon = column_info(upgraded_engine, SCHEMA_PRODUCT, "weather_sites", "site_long")

    assert wsi is not None
    assert lat is not None
    assert lon is not None

    assert wsi["nullable"] is False
    assert lat["nullable"] is False
    assert lon["nullable"] is False

    # loose type checks (avoid dialect quirks)
    assert isinstance(wsi["type"], sa.types.String)
    assert isinstance(lat["type"], sa.types.Float)
    assert isinstance(lon["type"], sa.types.Float)

    # --- unique constraint on (site_lat, site_long) ---
    insp = inspect(upgraded_engine)
    uqs = insp.get_unique_constraints("weather_sites", schema=SCHEMA_PRODUCT)
    uq_names = {u["name"] for u in uqs}
    assert "uq_weather_sites_lat_long" in uq_names

    # --- indexes ---
    ws_indexes = index_names(upgraded_engine, SCHEMA_PRODUCT, "weather_sites")
    assert "ix_weather_sites_lat_long" in ws_indexes

    assets_indexes = index_names(upgraded_engine, SCHEMA_OPENSTEF, "assets")
    assert "ix_assets_weather_site_id" in assets_indexes

    # --- FK assets.weather_site_id -> product.weather_sites.weather_site_id ---
    fks = fk_constraints(upgraded_engine, SCHEMA_OPENSTEF, "assets")
    fk = next((f for f in fks if f.get("name") == "fk_assets_weather_site_id"), None)
    assert fk is not None

    # referred table/schema/columns
    assert fk["referred_schema"] == SCHEMA_PRODUCT
    assert fk["referred_table"] == "weather_sites"
    assert fk["constrained_columns"] == ["weather_site_id"]
    assert fk["referred_columns"] == ["weather_site_id"]


def test_rev7_removed_on_downgrade(alembic_cfg, upgraded_engine):
    """
    Downgrade from rev7 -> rev6.

      - FK constraint is removed
      - indexes are removed
      - product.weather_sites table is removed
      - openstef.assets.weather_site_id column remains (it was added in rev6)
    """
    command.upgrade(alembic_cfg, "rev7")
    command.downgrade(alembic_cfg, "rev6")

    # table gone
    assert table_exists(upgraded_engine, SCHEMA_PRODUCT, "weather_sites") is False

    # assets.weather_site_id column still exists (rev6)
    assert (
        column_info(upgraded_engine, SCHEMA_OPENSTEF, "assets", "weather_site_id")
        is not None
    )

    # assets index removed
    assets_indexes = index_names(upgraded_engine, SCHEMA_OPENSTEF, "assets")
    assert "ix_assets_weather_site_id" not in assets_indexes

    # FK removed
    fks = fk_constraints(upgraded_engine, SCHEMA_OPENSTEF, "assets")
    assert all(f.get("name") != "fk_assets_weather_site_id" for f in fks)
