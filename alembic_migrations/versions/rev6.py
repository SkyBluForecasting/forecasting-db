"""rev6: add pv asset type + lat/long + weather_site_id to openstef.assets.

Revision ID: rev6
Revises: rev5
Create Date: 2026-02-08 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "rev6"
down_revision = "rev5"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Add enum value to existing Postgres enum
    op.execute("ALTER TYPE public.asset_type_enum ADD VALUE IF NOT EXISTS 'pv'")

    # 2) Add new nullable columns to openstef.assets
    op.add_column(
        "assets", sa.Column("latitude", sa.Float(), nullable=True), schema="openstef"
    )
    op.add_column(
        "assets", sa.Column("longitude", sa.Float(), nullable=True), schema="openstef"
    )
    op.add_column(
        "assets",
        sa.Column("weather_site_id", sa.String(), nullable=True),
        schema="openstef",
    )


def downgrade():
    op.drop_column("assets", "weather_site_id", schema="openstef")
    op.drop_column("assets", "longitude", schema="openstef")
    op.drop_column("assets", "latitude", schema="openstef")

    # NOTE: Did NOT remove 'pv' from the enum.
