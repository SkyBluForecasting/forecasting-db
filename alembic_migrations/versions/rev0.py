"""Initial schema."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "rev0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # --- Forecasts ---
    op.create_table(
        "forecasts",
        sa.Column("asset_uuid", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_uuid", UUID(as_uuid=True), nullable=False),
        sa.Column("forecast_kw", sa.Float, nullable=False),
        sa.PrimaryKeyConstraint("asset_uuid", "timestamp", "forecast_uuid"),
    )
    op.create_index("ix_forecasts_forecast_uuid", "forecasts", ["forecast_uuid"])

    # --- ForecastRuns ---
    op.create_table(
        "forecast_runs",
        sa.Column(
            "forecast_uuid", UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("run_uuid", sa.String(50), nullable=False),
        sa.Column("asset_uuid", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("frequency_min", sa.Float, nullable=False),
    )
    op.create_index("ix_forecast_runs_asset_uuid", "forecast_runs", ["asset_uuid"])

    # --- Constraints ---
    op.create_table(
        "constraints",
        sa.Column("asset_uuid", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_uuid", UUID(as_uuid=True), nullable=False),
        sa.Column("constraint_kw", sa.Float, nullable=False),
        sa.PrimaryKeyConstraint("asset_uuid", "timestamp", "forecast_uuid"),
    )
    op.create_index("ix_constraints_forecast_uuid", "constraints", ["forecast_uuid"])

    # --- Measurements ---
    op.create_table(
        "measurements",
        sa.Column("asset_uuid", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.PrimaryKeyConstraint("asset_uuid", "timestamp", "metric"),
    )


def downgrade():
    op.drop_table("measurements")
    op.drop_index("ix_constraints_forecast_uuid", table_name="constraints")
    op.drop_table("constraints")
    op.drop_index("ix_forecast_runs_asset_uuid", table_name="forecast_runs")
    op.drop_table("forecast_runs")
    op.drop_index("ix_forecasts_forecast_uuid", table_name="forecasts")
    op.drop_table("forecasts")
