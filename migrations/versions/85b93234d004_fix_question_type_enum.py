"""fix question_type enum

Revision ID: 85b93234d004
Revises: 4ba1b6a704b0
Create Date: 2026-03-07 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85b93234d004'
down_revision = '4ba1b6a704b0'
branch_labels = None
depends_on = None


def upgrade():
    # Manual SQL to update ENUM for MySQL
    op.execute("ALTER TABLE questions MODIFY COLUMN question_type ENUM('MULTIPLE_CHOICE', 'TRUE_FALSE', 'DROPDOWN', 'CHECKBOX', 'LONG_TEXT', 'UPLOAD') NOT NULL")


def downgrade():
    # Revert to previous enum values (careful: this might fail if new values are in use)
    op.execute("ALTER TABLE questions MODIFY COLUMN question_type ENUM('MULTIPLE_CHOICE', 'TRUE_FALSE', 'LONG_TEXT') NOT NULL")
