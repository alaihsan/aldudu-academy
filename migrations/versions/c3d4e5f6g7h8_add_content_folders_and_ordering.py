"""add content folders and ordering

Revision ID: c3d4e5f6g7h8
Revises: a4bfedd613ff
Create Date: 2026-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'a4bfedd613ff'
branch_labels = None
depends_on = None


def upgrade():
    # Create content_folders table
    op.create_table('content_folders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('parent_folder_id', sa.Integer(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['parent_folder_id'], ['content_folders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('content_folders', schema=None) as batch_op:
        batch_op.create_index('ix_content_folders_course_id', ['course_id'])
        batch_op.create_index('ix_content_folders_parent_folder_id', ['parent_folder_id'])

    # Add folder_id and order to quizzes
    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('folder_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('order', sa.Integer(), nullable=False, server_default='0'))
        batch_op.create_index('ix_quizzes_folder_id', ['folder_id'])
        batch_op.create_foreign_key('fk_quizzes_folder_id', 'content_folders', ['folder_id'], ['id'])

    # Add folder_id and order to assignments
    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('folder_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('order', sa.Integer(), nullable=False, server_default='0'))
        batch_op.create_index('ix_assignments_folder_id', ['folder_id'])
        batch_op.create_foreign_key('fk_assignments_folder_id', 'content_folders', ['folder_id'], ['id'])

    # Add folder_id and order to files
    with op.batch_alter_table('files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('folder_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('order', sa.Integer(), nullable=False, server_default='0'))
        batch_op.create_index('ix_files_folder_id', ['folder_id'])
        batch_op.create_foreign_key('fk_files_folder_id', 'content_folders', ['folder_id'], ['id'])

    # Add folder_id and order to links
    with op.batch_alter_table('links', schema=None) as batch_op:
        batch_op.add_column(sa.Column('folder_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('order', sa.Integer(), nullable=False, server_default='0'))
        batch_op.create_index('ix_links_folder_id', ['folder_id'])
        batch_op.create_foreign_key('fk_links_folder_id', 'content_folders', ['folder_id'], ['id'])


def downgrade():
    with op.batch_alter_table('links', schema=None) as batch_op:
        batch_op.drop_constraint('fk_links_folder_id', type_='foreignkey')
        batch_op.drop_index('ix_links_folder_id')
        batch_op.drop_column('order')
        batch_op.drop_column('folder_id')

    with op.batch_alter_table('files', schema=None) as batch_op:
        batch_op.drop_constraint('fk_files_folder_id', type_='foreignkey')
        batch_op.drop_index('ix_files_folder_id')
        batch_op.drop_column('order')
        batch_op.drop_column('folder_id')

    with op.batch_alter_table('assignments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_assignments_folder_id', type_='foreignkey')
        batch_op.drop_index('ix_assignments_folder_id')
        batch_op.drop_column('order')
        batch_op.drop_column('folder_id')

    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.drop_constraint('fk_quizzes_folder_id', type_='foreignkey')
        batch_op.drop_index('ix_quizzes_folder_id')
        batch_op.drop_column('order')
        batch_op.drop_column('folder_id')

    op.drop_table('content_folders')
