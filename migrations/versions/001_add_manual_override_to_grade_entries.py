"""
Add manual_override column to grade_entries table

Revision ID: 001
Revises: a1b2c3d4e5f8
Create Date: 2026-03-23

This migration adds the manual_override flag to GradeEntry model.
When True, protects the grade from being overwritten by automatic quiz sync.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = 'a1b2c3d4e5f8'  # Latest migration: add is_archived to quizzes
branch_labels = None
depends_on = None


def upgrade():
    # Add manual_override column to grade_entries table
    op.add_column(
        'grade_entries',
        sa.Column('manual_override', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade():
    # Remove manual_override column from grade_entries table
    op.drop_column('grade_entries', 'manual_override')
