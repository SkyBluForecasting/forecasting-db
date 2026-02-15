"""rev7: add product.weather_sites + FK from openstef.assets.weather_site_id.

Revision ID: rev7
Revises: rev6
Create Date: 2026-02-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "rev7"
down_revision = "rev6"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "weather_sites",
        sa.Column("weather_site_id", sa.String(), primary_key=True, nullable=False),
        sa.Column("site_lat", sa.Float(), nullable=False),
        sa.Column("site_long", sa.Float(), nullable=False),
        sa.UniqueConstraint("site_lat", "site_long", name="uq_weather_sites_lat_long"),
        schema="product",
    )

    # Useful for lookup-by-coordinates
    op.create_index(
        "ix_weather_sites_lat_long",
        "weather_sites",
        ["site_lat", "site_long"],
        unique=False,
        schema="product",
    )

    # Index assets.weather_site_id
    op.create_index(
        "ix_assets_weather_site_id",
        "assets",
        ["weather_site_id"],
        unique=False,
        schema="openstef",
    )

    # FK for DB-level integrity
    op.create_foreign_key(
        "fk_assets_weather_site_id",
        source_table="assets",
        referent_table="weather_sites",
        local_cols=["weather_site_id"],
        remote_cols=["weather_site_id"],
        source_schema="openstef",
        referent_schema="product",
    )


def downgrade():
    op.drop_constraint(
        "fk_assets_weather_site_id",
        "assets",
        schema="openstef",
        type_="foreignkey",
    )

    op.drop_index("ix_assets_weather_site_id", table_name="assets", schema="openstef")
    op.drop_index(
        "ix_weather_sites_lat_long", table_name="weather_sites", schema="product"
    )

    op.drop_table("weather_sites", schema="product")
