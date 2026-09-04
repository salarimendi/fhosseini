"""add visit table

Revision ID: 20251002_add_visit_table
Revises: 20240610_add_research_images
Create Date: 2025-10-02 12:45:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251002_add_visit_table'
down_revision = '20240610_add_research_images'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'visits',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.String(length=10), nullable=False, unique=True),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0')
    )


def downgrade():
    op.drop_table('visits')