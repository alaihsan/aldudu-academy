"""add gradebook models

Revision ID: a1b2c3d4e5f7
Revises: 21972951625e
Create Date: 2025-03-16 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = '21972951625e'
branch_labels = None
depends_on = None


def upgrade():
    # Create grade_categories table
    op.create_table('grade_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category_type', sa.Enum('FORMATIF', 'SUMATIF', 'SIKAP', 'PORTFOLIO', name='gradecategorytype'), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_grade_categories_course_id'), 'grade_categories', ['course_id'], unique=False)

    # Create learning_objectives table (CP)
    op.create_table('learning_objectives',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'course_id', name='uq_cp_code_course'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_learning_objectives_course_id'), 'learning_objectives', ['course_id'], unique=False)

    # Create learning_goals table (TP)
    op.create_table('learning_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('learning_objective_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'learning_objective_id', name='uq_tp_code_lo'),
        sa.ForeignKeyConstraint(['learning_objective_id'], ['learning_objectives.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_learning_goals_learning_objective_id'), 'learning_goals', ['learning_objective_id'], unique=False)

    # Create grade_items table
    op.create_table('grade_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('learning_objective_id', sa.Integer(), nullable=True),
        sa.Column('learning_goal_id', sa.Integer(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['category_id'], ['grade_categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['learning_objective_id'], ['learning_objectives.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['learning_goal_id'], ['learning_goals.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_grade_items_category_id'), 'grade_items', ['category_id'], unique=False)
    op.create_index(op.f('ix_grade_items_learning_objective_id'), 'grade_items', ['learning_objective_id'], unique=False)
    op.create_index(op.f('ix_grade_items_learning_goal_id'), 'grade_items', ['learning_goal_id'], unique=False)
    op.create_index(op.f('ix_grade_items_course_id'), 'grade_items', ['course_id'], unique=False)
    op.create_index(op.f('ix_grade_items_quiz_id'), 'grade_items', ['quiz_id'], unique=False)

    # Create grade_entries table
    op.create_table('grade_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grade_item_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('percentage', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('graded_at', sa.DateTime(), nullable=True),
        sa.Column('graded_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('grade_item_id', 'student_id', name='uq_grade_item_student'),
        sa.ForeignKeyConstraint(['grade_item_id'], ['grade_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['graded_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_grade_entries_grade_item_id'), 'grade_entries', ['grade_item_id'], unique=False)
    op.create_index(op.f('ix_grade_entries_student_id'), 'grade_entries', ['student_id'], unique=False)
    op.create_index(op.f('ix_grade_entries_graded_by'), 'grade_entries', ['graded_by'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_grade_entries_graded_by'), table_name='grade_entries')
    op.drop_index(op.f('ix_grade_entries_student_id'), table_name='grade_entries')
    op.drop_index(op.f('ix_grade_entries_grade_item_id'), table_name='grade_entries')
    op.drop_table('grade_entries')
    
    op.drop_index(op.f('ix_grade_items_quiz_id'), table_name='grade_items')
    op.drop_index(op.f('ix_grade_items_course_id'), table_name='grade_items')
    op.drop_index(op.f('ix_grade_items_learning_goal_id'), table_name='grade_items')
    op.drop_index(op.f('ix_grade_items_learning_objective_id'), table_name='grade_items')
    op.drop_index(op.f('ix_grade_items_category_id'), table_name='grade_items')
    op.drop_table('grade_items')
    
    op.drop_index(op.f('ix_learning_goals_learning_objective_id'), table_name='learning_goals')
    op.drop_table('learning_goals')
    
    op.drop_index(op.f('ix_learning_objectives_course_id'), table_name='learning_objectives')
    op.drop_table('learning_objectives')
    
    op.drop_index(op.f('ix_grade_categories_course_id'), table_name='grade_categories')
    op.drop_table('grade_categories')
