"""Add article_media table (metadata of uploaded article files)."""

from alembic import op
import sqlalchemy as sa


revision = 'e7a1c5b30f42'
down_revision = 'd24c49c8a2e1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'article_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_name', sa.String(length=255), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id']),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_article_media_article_id'), 'article_media', ['article_id'], unique=False)
    op.create_index(op.f('ix_article_media_filename'), 'article_media', ['filename'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_article_media_filename'), table_name='article_media')
    op.drop_index(op.f('ix_article_media_article_id'), table_name='article_media')
    op.drop_table('article_media')
