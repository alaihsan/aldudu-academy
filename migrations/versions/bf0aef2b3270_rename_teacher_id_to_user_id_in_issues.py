"""rename teacher_id to user_id in issues

Revision ID: bf0aef2b3270
Revises: 0cffdbdf28b5
Create Date: 2026-03-07 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf0aef2b3270'
down_revision = '0cffdbdf28b5'
branch_labels = None
depends_on = None


def upgrade():
    # MySQL specific: drop FK, rename column, add FK
    op.execute("ALTER TABLE issues DROP FOREIGN KEY issues_ibfk_1")
    op.execute("ALTER TABLE issues CHANGE COLUMN teacher_id user_id INT NOT NULL")
    op.execute("ALTER TABLE issues ADD CONSTRAINT issues_user_ibfk_1 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE")


def downgrade():
    op.execute("ALTER TABLE issues DROP FOREIGN KEY issues_user_ibfk_1")
    op.execute("ALTER TABLE issues CHANGE COLUMN user_id teacher_id INT NOT NULL")
    op.execute("ALTER TABLE issues ADD CONSTRAINT issues_ibfk_1 FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE")
