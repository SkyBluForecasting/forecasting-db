"""rev3: remove char limit on asset_uuid, asset_name, and parent_uuid in the Assets table.

Revision ID: rev3
Revises: rev2
Create Date: 2025-12-29 11:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "rev3"
down_revision = "rev2"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("assets", "asset_uuid", type_=sa.String(), schema="openstef")
    op.alter_column("assets", "name", type_=sa.String(), schema="openstef")
    op.alter_column("assets", "parent_uuid", type_=sa.String(), schema="openstef")


def downgrade():
    op.alter_column("assets", "asset_uuid", type_=sa.String(50), schema="openstef")
    op.alter_column("assets", "name", type_=sa.String(100), schema="openstef")
    op.alter_column("assets", "parent_uuid", type_=sa.String(50), schema="openstef")
