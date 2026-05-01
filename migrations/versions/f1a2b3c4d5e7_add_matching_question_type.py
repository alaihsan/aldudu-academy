"""add matching question type

Revision ID: f1a2b3c4d5e7
Revises: f1a2b3c4d5e6
Create Date: 2026-05-01 00:00:00.000000

"""
from alembic import op


revision = 'f1a2b3c4d5e7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE questions MODIFY COLUMN question_type ENUM('MULTIPLE_CHOICE', 'TRUE_FALSE', 'DROPDOWN', 'CHECKBOX', 'LONG_TEXT', 'UPLOAD', 'MATCHING') NOT NULL")


def downgrade():
    op.execute("ALTER TABLE questions MODIFY COLUMN question_type ENUM('MULTIPLE_CHOICE', 'TRUE_FALSE', 'DROPDOWN', 'CHECKBOX', 'LONG_TEXT', 'UPLOAD') NOT NULL")
