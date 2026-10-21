"""Add site_settings table (key/value site settings)."""

from alembic import op
import sqlalchemy as sa


revision = 'f3a9d1c27b64'
down_revision = 'e7a1c5b30f42'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'site_settings',
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('key'),
    )


def downgrade():
    op.drop_table('site_settings')
