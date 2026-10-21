"""Seed any missing manuscript version codes."""

from alembic import op
import sqlalchemy as sa


revision = 'd24c49c8a2e1'
down_revision = 'b90e9f2351ac'
branch_labels = None
depends_on = None


def upgrade():
    versions_table = sa.table(
        'versions',
        sa.column('name', sa.String(length=20)),
        sa.column('sort_order', sa.Integer()),
    )
    connection = op.get_bind()
    existing_names = set(connection.execute(
        sa.select(versions_table.c.name)
    ).scalars())

    configured_versions = [
        {'name': 'کا', 'sort_order': 1},
        {'name': 'اد', 'sort_order': 2},
        {'name': 'مر', 'sort_order': 3},
        {'name': 'خا', 'sort_order': 4},
        {'name': 'اح', 'sort_order': 5},
        {'name': 'می', 'sort_order': 6},
        {'name': 'مد', 'sort_order': 7},
        {'name': 'مل', 'sort_order': 8},
        {'name': 'آس', 'sort_order': 9},
    ]
    missing_versions = [
        version for version in configured_versions
        if version['name'] not in existing_names
    ]

    if missing_versions:
        op.bulk_insert(versions_table, missing_versions)


def downgrade():
    pass