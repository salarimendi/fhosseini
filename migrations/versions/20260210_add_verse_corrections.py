"""add verse_corrections table

Revision ID: 20260210_add_verse_corrections
Revises: 20240610_add_research_images
Create Date: 2026-02-10 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260210_add_verse_corrections'
down_revision = '20240610_add_research_images'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'verse_corrections',

        sa.Column('id', sa.Integer(), primary_key=True),

        sa.Column(
            'verse_id',
            sa.Integer(),
            sa.ForeignKey('verses.id', ondelete='CASCADE'),
            nullable=False
        ),

        sa.Column('field_name', sa.String(length=20), nullable=False),

        sa.Column('old_text', sa.Text()),
        sa.Column('new_text', sa.Text(), nullable=False),

        sa.Column(
            'correction_type',
            sa.String(length=30),
            nullable=False,
            server_default='text'
        ),

        sa.Column('note', sa.Text()),

        sa.Column(
            'created_by',
            sa.Integer(),
            sa.ForeignKey('users.id')
        ),

        sa.Column('created_at', sa.DateTime()),

        sa.Column(
            'is_approved',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('0')
        ),

        sa.Column(
            'approved_by',
            sa.Integer(),
            sa.ForeignKey('users.id')
        ),

        sa.Column('approved_at', sa.DateTime()),
    )

    # ایندکس برای سرعت
    op.create_index(
        'ix_verse_corrections_verse_id',
        'verse_corrections',
        ['verse_id']
    )


def downgrade():
    op.drop_index('ix_verse_corrections_verse_id', table_name='verse_corrections')
    op.drop_table('verse_corrections')
