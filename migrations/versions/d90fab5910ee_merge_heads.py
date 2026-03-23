"""merge heads

Revision ID: d90fab5910ee
Revises: 7400ff3bd702, a1b2c3d4e5f8, c9d8e7f6a5b4
Create Date: 2026-03-23 14:16:50.487872

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd90fab5910ee'
down_revision = ('7400ff3bd702', 'a1b2c3d4e5f8', 'c9d8e7f6a5b4')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
