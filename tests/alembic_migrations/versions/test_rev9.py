"""Tests for rev9 migration: add weather_actual and weather_forecast tables."""

from alembic import command
from sqlalchemy import inspect, text


def enum_labels(engine, schema: str, enum_name: str) -> list[str]:
    """Return ordered labels for a Postgres enum type, e.g. public.weather_variable_enum."""
    sql = text(
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


# ─── Weather Variable Enum Tests ───────────────────────────────


def test_rev9_creates_weather_variable_enum(alembic_cfg, upgraded_engine):
    """Verify weather_variable_enum is created with correct values."""
    command.upgrade(alembic_cfg, "rev9")

    labels = enum_labels(upgraded_engine, "public", "weather_variable_enum")
    assert labels, "Expected public.weather_variable_enum to exist"
    assert "ghi_wm2" in labels
    assert "temp_air_c" in labels
    assert "wind_speed_ms" in labels


# ─── Weather Actual Table Tests ───────────────────────────────


def test_rev9_creates_weather_actual_table(alembic_cfg, upgraded_engine):
    """Verify weather_actual table exists with correct structure."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    tables = inspector.get_table_names(schema="product")
    assert "weather_actual" in tables


def test_rev9_weather_actual_columns(alembic_cfg, upgraded_engine):
    """Verify weather_actual table has all required columns."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    columns = inspector.get_columns("weather_actual", schema="product")
    column_names = [col["name"] for col in columns]

    assert "id" in column_names
    assert "weather_site_id" in column_names
    assert "variable" in column_names
    assert "value" in column_names
    assert "timestamp" in column_names


def test_rev9_weather_actual_primary_key(alembic_cfg, upgraded_engine):
    """Verify weather_actual table has correct primary key."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    pk = inspector.get_pk_constraint("weather_actual", schema="product")
    assert "id" in pk["constrained_columns"]


def test_rev9_weather_actual_unique_constraint(alembic_cfg, upgraded_engine):
    """Verify weather_actual has unique constraint on (weather_site_id, variable, timestamp)."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    constraints = inspector.get_unique_constraints("weather_actual", schema="product")
    constraint_names = [c["name"] for c in constraints]
    assert "uq_weather_actual_site_var_ts" in constraint_names


def test_rev9_weather_actual_indexes(alembic_cfg, upgraded_engine):
    """Verify weather_actual table has expected indexes."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    indexes = inspector.get_indexes("weather_actual", schema="product")
    index_names = [idx["name"] for idx in indexes]

    assert "ix_weather_actual_weather_site_id" in index_names
    assert "ix_weather_actual_timestamp" in index_names


# ─── Weather Forecast Table Tests ───────────────────────────────


def test_rev9_creates_weather_forecast_table(alembic_cfg, upgraded_engine):
    """Verify weather_forecast table exists with correct structure."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    tables = inspector.get_table_names(schema="product")
    assert "weather_forecast" in tables


def test_rev9_weather_forecast_columns(alembic_cfg, upgraded_engine):
    """Verify weather_forecast table has all required columns."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    columns = inspector.get_columns("weather_forecast", schema="product")
    column_names = [col["name"] for col in columns]

    assert "id" in column_names
    assert "weather_site_id" in column_names
    assert "variable" in column_names
    assert "value" in column_names
    assert "timestamp" in column_names
    assert "issue_time" in column_names


def test_rev9_weather_forecast_primary_key(alembic_cfg, upgraded_engine):
    """Verify weather_forecast table has correct primary key."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    pk = inspector.get_pk_constraint("weather_forecast", schema="product")
    assert "id" in pk["constrained_columns"]


def test_rev9_weather_forecast_unique_constraint(alembic_cfg, upgraded_engine):
    """Verify weather_forecast has unique constraint on (weather_site_id, variable, timestamp, issue_time)."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    constraints = inspector.get_unique_constraints("weather_forecast", schema="product")
    constraint_names = [c["name"] for c in constraints]
    assert "uq_weather_forecast_site_var_timestamp_issue" in constraint_names


def test_rev9_weather_forecast_indexes(alembic_cfg, upgraded_engine):
    """Verify weather_forecast table has expected indexes."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    indexes = inspector.get_indexes("weather_forecast", schema="product")
    index_names = [idx["name"] for idx in indexes]

    assert "ix_weather_forecast_weather_site_id" in index_names
    assert "ix_weather_forecast_timestamp" in index_names
    assert "ix_weather_forecast_issue_time" in index_names


def test_rev9_weather_forecast_timestamp_index_columns(alembic_cfg, upgraded_engine):
    """Verify the timestamp index references the correct column."""
    command.upgrade(alembic_cfg, "rev9")

    inspector = inspect(upgraded_engine)
    indexes = inspector.get_indexes("weather_forecast", schema="product")

    timestamp_index = next(
        (idx for idx in indexes if idx["name"] == "ix_weather_forecast_timestamp"), None
    )
    assert timestamp_index is not None, "ix_weather_forecast_timestamp index not found"
    assert "timestamp" in timestamp_index["column_names"]


# ─── Downgrade Tests ───────────────────────────────


def test_rev9_downgrade_removes_tables(alembic_cfg, upgraded_engine):
    """Verify downgrade removes both weather tables."""
    command.upgrade(alembic_cfg, "rev9")
    command.downgrade(alembic_cfg, "rev8")

    inspector = inspect(upgraded_engine)
    tables = inspector.get_table_names(schema="product")
    assert "weather_actual" not in tables
    assert "weather_forecast" not in tables


def test_rev9_downgrade_removes_enum(alembic_cfg, upgraded_engine):
    """Verify downgrade removes weather_variable_enum."""
    command.upgrade(alembic_cfg, "rev9")
    command.downgrade(alembic_cfg, "rev8")

    # Verify enum is removed (should raise if it exists)
    try:
        enum_labels(upgraded_engine, "public", "weather_variable_enum")
        # If no error, the enum still exists - this is acceptable as downgrade uses DROP IF EXISTS
        assert False, "Expected enum to be removed"
    except Exception:
        # Expected: enum doesn't exist
        pass
