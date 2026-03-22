"""add is_archived to quizzes

Revision ID: a1b2c3d4e5f8
Revises: dd887f4e556b
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f8'
down_revision = 'dd887f4e556b'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_archived column to quizzes table
    op.add_column('quizzes', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.false()))
    
    # Create index for better query performance
    op.create_index('idx_quizzes_is_archived', 'quizzes', ['is_archived'])
    op.create_index('idx_quizzes_course_archived', 'quizzes', ['course_id', 'is_archived'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_quizzes_course_archived', table_name='quizzes')
    op.drop_index('idx_quizzes_is_archived', table_name='quizzes')
    
    # Drop column
    op.drop_column('quizzes', 'is_archived')
