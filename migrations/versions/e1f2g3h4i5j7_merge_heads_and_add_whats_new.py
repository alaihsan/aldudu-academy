"""merge heads and add whats_new table

Revision ID: e1f2g3h4i5j7
Revises: d90fab5910ee, 001
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1f2g3h4i5j7'
down_revision = ('d90fab5910ee', '001')
branch_labels = None
depends_on = None


def upgrade():
    # Create whats_new table
    op.create_table('whats_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on created_at for faster ordering
    op.create_index('ix_whats_new_created_at', 'whats_new', ['created_at'])
    op.create_index('ix_whats_new_is_published', 'whats_new', ['is_published'])


def downgrade():
    op.drop_index('ix_whats_new_is_published', table_name='whats_new')
    op.drop_index('ix_whats_new_created_at', table_name='whats_new')
    op.drop_table('whats_new')
