"""Add section + activity fields to articles / article_categories (وبلاگ فعالیت‌ها)."""

from alembic import op
import sqlalchemy as sa


revision = 'b5d7e3f10a28'
down_revision = 'f3a9d1c27b64'
branch_labels = None
depends_on = None


def upgrade():
    for table in ('article_categories', 'articles'):
        op.add_column(table, sa.Column('section', sa.String(length=20), nullable=False, server_default='articles'))
        op.create_index(op.f(f'ix_{table}_section'), table, ['section'], unique=False)
    op.add_column('articles', sa.Column('stage_label', sa.String(length=120), nullable=True))
    op.add_column('articles', sa.Column('contributors', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('video_url', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('articles', 'video_url')
    op.drop_column('articles', 'contributors')
    op.drop_column('articles', 'stage_label')
    for table in ('articles', 'article_categories'):
        op.drop_index(op.f(f'ix_{table}_section'), table_name=table)
        op.drop_column(table, 'section')
