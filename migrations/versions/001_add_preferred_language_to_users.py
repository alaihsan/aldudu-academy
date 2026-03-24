"""add preferred language to users

Revision ID: 001
Revises: a4bfedd613ff
Create Date: 2025-03-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = 'a4bfedd613ff'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists (for idempotent migration)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'preferred_language' not in columns:
        # Add preferred_language column to users table
        op.add_column('users', sa.Column('preferred_language', sa.String(length=10), nullable=True, default='id'))
        # Set default value for existing users
        op.execute("UPDATE users SET preferred_language = 'id' WHERE preferred_language IS NULL")


def downgrade():
    # Remove preferred_language column from users table
    op.drop_column('users', 'preferred_language')
