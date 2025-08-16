"""add research_images table

Revision ID: 20240610_add_research_images
Revises: ae847c4565e9
Create Date: 2024-06-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '20240610_add_research_images'
down_revision = 'ae847c4565e9'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'research_images',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('comment_id', sa.Integer(), sa.ForeignKey('comments.id'), nullable=False),
        sa.Column('subtopic_index', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255)),
        sa.Column('caption', sa.String(length=500)),
        sa.Column('file_size', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

def downgrade():
    op.drop_table('research_images') 