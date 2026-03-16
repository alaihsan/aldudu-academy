"""add kbm notes model

Revision ID: b2c3d4e5f6g8
Revises: a1b2c3d4e5f7
Create Date: 2025-03-16 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g8'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for activity_type
    activity_type = sa.Enum('TEORI', 'PRAKTIKUM', 'UJIAN', 'TUGAS', 'REVIEW', 'LAINNYA', name='kbmactivitytype')
    activity_type.create(op.get_bind())

    # Create kbm_notes table
    op.create_table('kbm_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('activity_date', sa.DateTime(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('activity_type', activity_type, nullable=False, server_default='teori'),
        sa.Column('topic', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_kbm_notes_course_id'), 'kbm_notes', ['course_id'], unique=False)
    op.create_index(op.f('ix_kbm_notes_teacher_id'), 'kbm_notes', ['teacher_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_kbm_notes_teacher_id'), table_name='kbm_notes')
    op.drop_index(op.f('ix_kbm_notes_course_id'), table_name='kbm_notes')
    op.drop_table('kbm_notes')
    
    # Drop enum type
    activity_type = sa.Enum(name='kbmactivitytype')
    activity_type.drop(op.get_bind())
