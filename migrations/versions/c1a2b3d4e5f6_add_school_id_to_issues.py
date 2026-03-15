"""add school_id to issues table

Revision ID: c1a2b3d4e5f6
Revises: ac94c9116a87
Create Date: 2026-03-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1a2b3d4e5f6'
down_revision = 'ac94c9116a87'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add school_id as nullable
    op.add_column('issues', sa.Column('school_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_issues_school_id'), 'issues', ['school_id'], unique=False)
    op.create_foreign_key('fk_issues_school_id', 'issues', 'schools', ['school_id'], ['id'])

    # Step 2: Backfill school_id from users table
    op.execute(
        "UPDATE issues SET school_id = (SELECT school_id FROM users WHERE users.id = issues.user_id)"
    )


def downgrade():
    op.drop_constraint('fk_issues_school_id', 'issues', type_='foreignkey')
    op.drop_index(op.f('ix_issues_school_id'), table_name='issues')
    op.drop_column('issues', 'school_id')
