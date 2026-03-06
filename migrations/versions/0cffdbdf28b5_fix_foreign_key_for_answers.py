"""fix foreign key for answers

Revision ID: 0cffdbdf28b5
Revises: 85b93234d004
Create Date: 2026-03-07 05:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0cffdbdf28b5'
down_revision = '85b93234d004'
branch_labels = None
depends_on = None


def upgrade():
    # MySQL specific: drop existing FK and add new one with ON DELETE SET NULL
    op.execute("ALTER TABLE answers DROP FOREIGN KEY answers_ibfk_2")
    op.execute("ALTER TABLE answers ADD CONSTRAINT answers_ibfk_2 FOREIGN KEY (selected_option_id) REFERENCES options(id) ON DELETE SET NULL")


def downgrade():
    op.execute("ALTER TABLE answers DROP FOREIGN KEY answers_ibfk_2")
    op.execute("ALTER TABLE answers ADD CONSTRAINT answers_ibfk_2 FOREIGN KEY (selected_option_id) REFERENCES options(id)")
