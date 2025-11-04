"""Add created_at and updated_at to quiz

Revision ID: 6d87cf6c7f0d
Revises:
Create Date: 2025-11-04 11:26:00.000000

"""
from alembic import op
import sqlalchemy as sa
import datetime

# revision identifiers, used by Alembic.
revision = '6d87cf6c7f0d'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add created_at and updated_at to quizzes
    op.add_column('quizzes', sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.datetime.utcnow))
    op.add_column('quizzes', sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow))

    # Add order, description, image_path to questions
    op.add_column('questions', sa.Column('order', sa.Integer(), nullable=False, default=1))
    op.add_column('questions', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('image_path', sa.String(length=500), nullable=True))

    # Add order to options
    op.add_column('options', sa.Column('order', sa.Integer(), nullable=False, default=1))

    # Create links table
    op.create_table('links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_links_course_id'), 'links', ['course_id'], unique=False)

    # Create files table
    op.create_table('files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('filename', sa.String(length=200), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_files_course_id'), 'files', ['course_id'], unique=False)

def downgrade():
    op.drop_table('files')
    op.drop_table('links')
    op.drop_column('options', 'order')
    op.drop_column('questions', 'image_path')
    op.drop_column('questions', 'description')
    op.drop_column('questions', 'order')
    op.drop_column('quizzes', 'updated_at')
    op.drop_column('quizzes', 'created_at')
