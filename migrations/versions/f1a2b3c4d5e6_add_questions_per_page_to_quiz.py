"""add questions_per_page to quiz

Revision ID: f1a2b3c4d5e6
Revises: e1f2g3h4i5j7
Create Date: 2026-05-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f1a2b3c4d5e6'
down_revision = 'e1f2g3h4i5j7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('questions_per_page', sa.Integer(), nullable=False, server_default='0'))

    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.alter_column('questions_per_page', server_default=None)


def downgrade():
    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.drop_column('questions_per_page')
