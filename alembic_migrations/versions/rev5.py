"""rev5: remove char limit on all asset_uuid FKs and make ForecastRun.model_run_id nullable.

Revision ID: rev5
Revises: rev4
Create Date: 2026-01-02 14:40:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "rev5"
down_revision = "rev4"
branch_labels = None
depends_on = None


def upgrade():
    # --- OpenSTEF schema ---
    # Remove VARCHAR(50) limit from asset_uuid columns
    for table in ["measurement", "prediction_job", "forecast_runs"]:
        op.alter_column(table, "asset_uuid", type_=sa.String(), schema="openstef")

    # Make model_run_id nullable in forecast_runs
    op.alter_column(
        "forecast_runs",
        "model_run_id",
        existing_type=sa.String(100),
        nullable=True,
        schema="openstef",
    )

    # --- Product schema ---
    op.alter_column("constraints", "asset_uuid", type_=sa.String(), schema="product")


def downgrade():
    # revert asset_uuid columns back to VARCHAR(50)
    for table in ["measurement", "prediction_job", "forecast_runs"]:
        op.alter_column(table, "asset_uuid", type_=sa.String(50), schema="openstef")

    # revert model_run_id to NOT NULL
    op.alter_column(
        "forecast_runs",
        "model_run_id",
        existing_type=sa.String(100),
        nullable=False,
        schema="openstef",
    )

    # revert constraints.asset_uuid back to VARCHAR(50)
    op.alter_column("constraints", "asset_uuid", type_=sa.String(50), schema="product")
