"""rev2: update assets table with measured, asset_type enum, and depth.

Revision ID: rev2
Revises: rev1
Create Date: 2025-12-27 11:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "rev2"
down_revision = "rev1"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add new Boolean column 'measured' with default False
    op.add_column(
        "assets",
        sa.Column("measured", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="openstef",
    )

    # 2. Add depth column with default 0
    op.add_column(
        "assets",
        sa.Column("depth", sa.Integer(), nullable=False, server_default="0"),
        schema="openstef",
    )

    # 3. Map 'substation' -> 'distribution_substation'
    op.execute(
        "UPDATE openstef.assets SET asset_type = 'distribution_substation' WHERE asset_type = 'substation';"
    )

    # 4. Create ENUM type for asset_type
    asset_type_enum = postgresql.ENUM(
        "system", "distribution_substation", name="asset_type_enum", create_type=True
    )
    asset_type_enum.create(op.get_bind(), checkfirst=True)

    # 5. Alter the asset_type column to use the new ENUM
    op.alter_column(
        "assets",
        "asset_type",
        type_=sa.Enum("system", "distribution_substation", name="asset_type_enum"),
        existing_type=sa.String(length=50),
        schema="openstef",
        nullable=False,
        postgresql_using="asset_type::asset_type_enum",
    )


def downgrade():
    # 1. Alter asset_type back to String
    op.alter_column(
        "assets",
        "asset_type",
        type_=sa.String(length=50),
        existing_type=sa.Enum(
            "system", "distribution_substation", name="asset_type_enum"
        ),
        schema="openstef",
        nullable=False,
        postgresql_using="asset_type::text",
    )

    # 2. Drop ENUM type
    asset_type_enum = postgresql.ENUM(
        "system", "distribution_substation", name="asset_type_enum"
    )
    asset_type_enum.drop(op.get_bind(), checkfirst=True)

    # 3. Drop depth column
    op.drop_column("assets", "depth", schema="openstef")

    # 4. Drop measured column
    op.drop_column("assets", "measured", schema="openstef")
