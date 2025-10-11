"""Initial schema with ForecastRun and updated references."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "rev0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # --- OpenSTEF schema ---
    op.execute("CREATE SCHEMA IF NOT EXISTS openstef;")

    # --- Assets ---
    op.create_table(
        "assets",
        sa.Column("asset_uuid", sa.String(50), primary_key=True),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("capacity_kw", sa.Float, nullable=True),
        sa.Column(
            "parent_uuid",
            sa.String(50),
            sa.ForeignKey("openstef.assets.asset_uuid", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="openstef",
    )

    # --- PredictionJob ---
    op.create_table(
        "prediction_job",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "asset_uuid",
            sa.String(50),
            sa.ForeignKey("openstef.assets.asset_uuid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model", sa.String(100)),
        sa.Column("horizon_minutes", sa.Integer),
        sa.Column("frequency_minutes", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("config", sa.JSON),
        schema="openstef",
    )

    # --- ForecastRun ---
    op.create_table(
        "forecast_runs",
        sa.Column("forecast_run_id", sa.String(50), primary_key=True),
        sa.Column(
            "prediction_job_id",
            sa.Integer,
            sa.ForeignKey("openstef.prediction_job.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model_run_id", sa.String(100)),
        sa.Column(
            "asset_uuid",
            sa.String(50),
            sa.ForeignKey("openstef.assets.asset_uuid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("start_time", sa.DateTime(timezone=True)),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("frequency_min", sa.Integer),
        schema="openstef",
    )

    # --- Forecast ---
    op.create_table(
        "forecast",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "forecast_run_id",
            sa.String(50),
            sa.ForeignKey("openstef.forecast_runs.forecast_run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_value", sa.Float, nullable=False),
        sa.Column("lower_q", sa.Float, nullable=True),
        sa.Column("upper_q", sa.Float, nullable=True),
        schema="openstef",
    )
    op.create_index(
        "ix_forecast_timestamp", "forecast", ["timestamp"], schema="openstef"
    )

    # --- Measurement ---
    op.create_table(
        "measurement",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "asset_uuid",
            sa.String(50),
            sa.ForeignKey("openstef.assets.asset_uuid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        schema="openstef",
    )
    op.create_index(
        "ix_measurement_timestamp", "measurement", ["timestamp"], schema="openstef"
    )

    # --- SkyBlu schema ---
    op.execute("CREATE SCHEMA IF NOT EXISTS product;")

    # --- Constraints ---
    op.create_table(
        "constraints",
        sa.Column(
            "constraint_uuid",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("asset_uuid", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "forecast_run_id",
            sa.String(50),
            sa.ForeignKey("openstef.forecast_runs.forecast_run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("constraint_kw", sa.Float, nullable=False),
        sa.UniqueConstraint(
            "asset_uuid",
            "timestamp",
            "forecast_run_id",
            name="uq_constraints_asset_ts_run",
        ),
        schema="product",
    )
    op.create_index(
        "ix_constraints_asset_ts",
        "constraints",
        ["asset_uuid", "timestamp"],
        schema="product",
    )


def downgrade():
    op.drop_index("ix_constraints_asset_ts", table_name="constraints", schema="product")
    op.drop_table("constraints", schema="product")

    op.drop_index("ix_measurement_timestamp", "measurement", schema="openstef")
    op.drop_table("measurement", schema="openstef")

    op.drop_index("ix_forecast_timestamp", "forecast", schema="openstef")
    op.drop_table("forecast", schema="openstef")

    op.drop_table("forecast_runs", schema="openstef")
    op.drop_table("prediction_job", schema="openstef")
    op.drop_table("assets", schema="openstef")

    op.execute("DROP SCHEMA IF EXISTS product;")
    op.execute("DROP SCHEMA IF EXISTS openstef;")
