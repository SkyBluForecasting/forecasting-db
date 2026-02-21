"""rev9: add weather_actual and weather_forecast tables.

Revision ID: rev9
Revises: rev8
Create Date: 2026-02-20 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "rev9"
down_revision = "rev8"
branch_labels = None
depends_on = None


def upgrade():
    # Create weather_variable_enum type
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE public.weather_variable_enum AS ENUM (
                'ghi_wm2',
                'temp_air_c',
                'wind_speed_ms'
            );
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
        """
    )

    # Create weather_actual table
    op.create_table(
        "weather_actual",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column(
            "weather_site_id",
            sa.String(),
            sa.ForeignKey("product.weather_sites.weather_site_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variable",
            postgresql.ENUM(
                "ghi_wm2",
                "temp_air_c",
                "wind_speed_ms",
                name="weather_variable_enum",
                schema="public",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "weather_site_id",
            "variable",
            "timestamp",
            name="uq_weather_actual_site_var_ts",
        ),
        schema="product",
    )
    op.create_index(
        "ix_weather_actual_weather_site_id",
        "weather_actual",
        ["weather_site_id"],
        schema="product",
    )
    op.create_index(
        "ix_weather_actual_timestamp",
        "weather_actual",
        ["timestamp"],
        schema="product",
    )

    # Create weather_forecast table
    op.create_table(
        "weather_forecast",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column(
            "weather_site_id",
            sa.String(),
            sa.ForeignKey("product.weather_sites.weather_site_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variable",
            postgresql.ENUM(
                "ghi_wm2",
                "temp_air_c",
                "wind_speed_ms",
                name="weather_variable_enum",
                schema="public",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issue_time", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "weather_site_id",
            "variable",
            "timestamp",
            "issue_time",
            name="uq_weather_forecast_site_var_timestamp_issue",
        ),
        schema="product",
    )
    op.create_index(
        "ix_weather_forecast_weather_site_id",
        "weather_forecast",
        ["weather_site_id"],
        schema="product",
    )
    op.create_index(
        "ix_weather_forecast_timestamp",
        "weather_forecast",
        ["timestamp"],
        schema="product",
    )
    op.create_index(
        "ix_weather_forecast_issue_time",
        "weather_forecast",
        ["issue_time"],
        schema="product",
    )


def downgrade():
    # Drop weather_forecast table
    op.drop_table("weather_forecast", schema="product")

    # Drop weather_actual table
    op.drop_table("weather_actual", schema="product")

    # Drop weather_variable_enum type
    op.execute("DROP TYPE IF EXISTS public.weather_variable_enum")
