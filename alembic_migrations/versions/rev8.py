"""rev8: add region to public.asset_type_enum.

Revision ID: rev8
Revises: rev7
Create Date: 2026-02-16 00:00:00.000000
"""

from alembic import op

revision = "rev8"
down_revision = "rev7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE public.asset_type_enum ADD VALUE IF NOT EXISTS 'region'")


def downgrade():
    raise NotImplementedError("Downgrade not supported for adding enum values.")
