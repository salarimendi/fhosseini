"""Add the manuscript version registry."""

from alembic import op
import sqlalchemy as sa


revision = 'b90e9f2351ac'
down_revision = '9c3488a27df0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=20), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    versions_table = sa.table(
        'versions',
        sa.column('name', sa.String(length=20)),
        sa.column('sort_order', sa.Integer()),
    )
    op.bulk_insert(versions_table, [
        {'name': 'کا', 'sort_order': 1},
        {'name': 'اد', 'sort_order': 2},
        {'name': 'مر', 'sort_order': 3},
        {'name': 'خا', 'sort_order': 4},
        {'name': 'اح', 'sort_order': 5},
        {'name': 'می', 'sort_order': 6},
        {'name': 'مد', 'sort_order': 7},
        {'name': 'مل', 'sort_order': 8},
        {'name': 'آس', 'sort_order': 9},
    ])


def downgrade():
    op.drop_table('versions')