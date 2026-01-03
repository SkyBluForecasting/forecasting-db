from alembic import command
from sqlalchemy import inspect

SCHEMA_OPENSTEF = "openstef"
SCHEMA_PRODUCT = "product"


def column_info(engine, schema, table, column):
    """Return column info from SQLAlchemy inspector."""
    inspector = inspect(engine)
    cols = inspector.get_columns(table, schema=schema)
    for col in cols:
        if col["name"] == column:
            return col
    return None


def test_rev5_columns_updated_on_upgrade(alembic_cfg, upgraded_engine):
    """Check rev5 columns updated correctly on upgrade."""
    # Upgrade to rev5
    command.upgrade(alembic_cfg, "rev5")

    # --- prediction_job.asset_uuid ---
    pj_col = column_info(
        upgraded_engine, SCHEMA_OPENSTEF, "prediction_job", "asset_uuid"
    )
    assert pj_col is not None
    assert pj_col["type"].length is None  # unlimited VARCHAR

    # --- measurement.asset_uuid ---
    m_col = column_info(upgraded_engine, SCHEMA_OPENSTEF, "measurement", "asset_uuid")
    assert m_col is not None
    assert m_col["type"].length is None

    # --- constraints.asset_uuid ---
    c_col = column_info(upgraded_engine, SCHEMA_PRODUCT, "constraints", "asset_uuid")
    assert c_col is not None
    assert c_col["type"].length is None

    # --- forecast_runs.model_run_id nullable ---
    fr_col = column_info(
        upgraded_engine, SCHEMA_OPENSTEF, "forecast_runs", "model_run_id"
    )
    assert fr_col is not None
    assert fr_col["nullable"] is True


def test_rev5_columns_changed_on_upgrade_and_reverted_on_downgrade(
    alembic_cfg, upgraded_engine
):
    """Check rev5 columns changed and revert correctly on downgrade."""
    # Upgrade to rev5
    command.upgrade(alembic_cfg, "rev5")

    # --- Check upgraded columns ---
    for table, col_name, schema in [
        ("measurement", "asset_uuid", SCHEMA_OPENSTEF),
        ("prediction_job", "asset_uuid", SCHEMA_OPENSTEF),
        ("constraints", "asset_uuid", SCHEMA_PRODUCT),
    ]:
        col = column_info(upgraded_engine, schema, table, col_name)
        assert col["type"].length is None  # unlimited VARCHAR

    fr_col = column_info(
        upgraded_engine, SCHEMA_OPENSTEF, "forecast_runs", "model_run_id"
    )
    assert fr_col["nullable"] is True

    # --- Downgrade rev5 -> rev4 ---
    command.downgrade(alembic_cfg, "rev4")

    # Check that the VARCHAR columns revert to 50-char limit
    for table, col_name, schema in [
        ("measurement", "asset_uuid", SCHEMA_OPENSTEF),
        ("prediction_job", "asset_uuid", SCHEMA_OPENSTEF),
        ("constraints", "asset_uuid", SCHEMA_PRODUCT),
    ]:
        col = column_info(upgraded_engine, schema, table, col_name)
        # Postgres inspector reports VARCHAR(n) as having length=n
        assert col["type"].length == 50

    fr_col = column_info(
        upgraded_engine, SCHEMA_OPENSTEF, "forecast_runs", "model_run_id"
    )
    assert fr_col["nullable"] is False
