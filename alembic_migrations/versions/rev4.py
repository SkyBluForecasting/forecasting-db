"""create mlflow schema.

Revision ID: rev4
Revises: rev3
Create Date: 2026-01-02 14:05:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "rev4"
down_revision = "rev3"
branch_labels = None
depends_on = None


def upgrade():
    # create mlflow schema if it doesn't exist
    op.execute("CREATE SCHEMA IF NOT EXISTS mlflow;")


def downgrade():
    # drop mlflow schema and all its tables
    op.execute("DROP SCHEMA IF EXISTS mlflow CASCADE;")
