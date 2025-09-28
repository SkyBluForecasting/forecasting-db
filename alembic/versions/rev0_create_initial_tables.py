"""create initial tables.

Revision ID: rev0
Revises:
Create Date: 2025-09-25 00:22:20.676981

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "rev0"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "forecasts",
        sa.Column("asset_uuid", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_kw", sa.Float, nullable=False),
        sa.Column("forecast_uuid", UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("asset_uuid", "timestamp", "forecast_uuid"),
    )
    op.create_index("ix_forecasts_forecast_uuid", "forecasts", ["forecast_uuid"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("forecasts")
