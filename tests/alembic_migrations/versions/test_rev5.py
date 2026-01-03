from alembic import command
from sqlalchemy import inspect

SCHEMA_NAME = "openstef"
TABLES_TO_CHECK = [
    "assets",
    "prediction_job",
    "forecast_runs",
    "measurement",
    "constraints",  # optional if you want to include product schema
]


def column_info(engine, schema, table, column):
    """Return column info from inspector."""
    inspector = inspect(engine)
    cols = inspector.get_columns(table, schema=schema)
    for col in cols:
        if col["name"] == column:
            return col
    return None


def test_rev5_columns_updated_on_upgrade(alembic_cfg, upgraded_engine):
    """Check asset_uuid and model_run_id columns updated as expected in rev5."""
    # Upgrade to rev5
    command.upgrade(alembic_cfg, "rev5")

    # --- assets table ---
    asset_uuid_col = column_info(upgraded_engine, SCHEMA_NAME, "assets", "asset_uuid")
    parent_uuid_col = column_info(upgraded_engine, SCHEMA_NAME, "assets", "parent_uuid")
    name_col = column_info(upgraded_engine, SCHEMA_NAME, "assets", "name")

    assert asset_uuid_col is not None
    assert asset_uuid_col["type"].length is None  # no length limit
    assert parent_uuid_col["type"].length is None
    assert name_col["type"].length is None

    # --- prediction_job table ---
    pj_col = column_info(upgraded_engine, SCHEMA_NAME, "prediction_job", "asset_uuid")
    assert pj_col is not None
    assert pj_col["type"].length is None

    # --- forecast_runs table ---
    fr_col = column_info(upgraded_engine, SCHEMA_NAME, "forecast_runs", "asset_uuid")
    mr_col = column_info(upgraded_engine, SCHEMA_NAME, "forecast_runs", "model_run_id")

    assert fr_col is not None
    assert fr_col["type"].length is None
    assert mr_col is not None
    assert mr_col["nullable"] is True  # model_run_id is now nullable

    # --- measurement table ---
    m_col = column_info(upgraded_engine, SCHEMA_NAME, "measurement", "asset_uuid")
    assert m_col is not None
    assert m_col["type"].length is None

    # --- constraints table (product schema) ---
    c_col = column_info(upgraded_engine, "product", "constraints", "asset_uuid")
    assert c_col is not None
    assert c_col["type"].length is None


def test_rev5_columns_changed_on_upgrade_and_reverted_on_downgrade(
    alembic_cfg, upgraded_engine
):
    """Check rev5 columns changed and reverted correctly."""
    # Upgrade to rev5
    command.upgrade(alembic_cfg, "rev5")

    # --- Check upgraded columns ---
    for table, col_name in [
        ("measurement", "asset_uuid"),
        ("prediction_job", "asset_uuid"),
        ("constraints", "asset_uuid"),
    ]:
        col = column_info(upgraded_engine, SCHEMA_NAME, table, col_name)
        assert col["type"].length is None  # unlimited VARCHAR

    # ForecastRun.model_run_id nullable
    mr_col = column_info(upgraded_engine, SCHEMA_NAME, "forecast_runs", "model_run_id")
    assert mr_col["nullable"] is True

    # --- Downgrade rev5 -> rev4 ---
    command.downgrade(alembic_cfg, "rev4")

    for table, col_name in [
        ("measurement", "asset_uuid"),
        ("prediction_job", "asset_uuid"),
        ("constraints", "asset_uuid"),
    ]:
        col = column_info(upgraded_engine, SCHEMA_NAME, table, col_name)
        assert col["type"].length == 50  # reverted to 50-char limit

    mr_col = column_info(upgraded_engine, SCHEMA_NAME, "forecast_runs", "model_run_id")
    assert mr_col["nullable"] is False
