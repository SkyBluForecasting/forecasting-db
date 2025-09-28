"""Initial schema."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "rev0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "forecasts",
        sa.Column("asset_uuid", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_kw", sa.Float, nullable=False),
        sa.Column("forecast_uuid", UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("asset_uuid", "timestamp", "forecast_uuid"),
    )
    op.create_index("ix_forecasts_forecast_uuid", "forecasts", ["forecast_uuid"])


def downgrade():
    op.drop_table("forecasts")
