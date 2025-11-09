"""Add forecast_errors table.

Revision ID: rev1
Revises: rev0
Create Date: 2025-11-07 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "rev1"
down_revision = "rev0"
branch_labels = None
depends_on = None


def upgrade():
    # --- ForecastErrors table ---
    op.create_table(
        "forecast_errors",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "forecast_run_id",
            sa.String(50),
            sa.ForeignKey("openstef.forecast_runs.forecast_run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error", sa.Float, nullable=False),
        sa.UniqueConstraint(
            "forecast_run_id", "timestamp", name="uq_forecast_errors_run_ts"
        ),
        sa.Index("ix_forecast_errors_run_ts", "forecast_run_id", "timestamp"),
        schema="product",
    )


def downgrade():
    op.drop_index(
        "ix_forecast_errors_run_ts", table_name="forecast_errors", schema="product"
    )
    op.drop_table("forecast_errors", schema="product")
