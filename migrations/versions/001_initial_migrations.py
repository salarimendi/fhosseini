"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial database schema"""
    
    # ایجاد جدول کاربران
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(80), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('reset_token', sa.String(100), nullable=True),
        sa.Column('reset_token_expires', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # ایجاد جدول نسخه‌ها
    op.create_table('versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ایجاد جدول عناوین اشعار
    op.create_table('titles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('garden', sa.Integer(), nullable=False),
        sa.Column('order_in_garden', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ایجاد جدول ابیات
    op.create_table('verses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title_id', sa.Integer(), nullable=False),
        sa.Column('order_in_title', sa.Integer(), nullable=False),
        sa.Column('verse_1', sa.Text(), nullable=False),
        sa.Column('verse_2', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['title_id'], ['titles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ایجاد جدول ابیات نسخه‌ها
    op.create_table('version_verses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('title_id', sa.Integer(), nullable=False),
        sa.Column('order_in_title', sa.Integer(), nullable=False),
        sa.Column('verse_1', sa.Text(), nullable=False),
        sa.Column('verse_2', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['version_id'], ['versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['title_id'], ['titles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ایجاد جدول نظرات پژوهشی
    op.create_table('comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title_id', sa.Integer(), nullable=False),
        sa.Column('verse_id', sa.Integer(), nullable=True),
        sa.Column('comment_type', sa.String(50), nullable=False, default='research'),  # research, criticism
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('is_approved', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['title_id'], ['titles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verse_id'], ['verses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ایجاد جدول ضبط‌های صوتی
    op.create_table('recordings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('mime_type', sa.String(50), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['title_id'], ['titles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ایجاد اندیس‌ها برای بهبود عملکرد
    op.create_index('idx_titles_garden', 'titles', ['garden'])
    op.create_index('idx_titles_order', 'titles', ['garden', 'order_in_garden'])
    op.create_index('idx_verses_title', 'verses', ['title_id'])
    op.create_index('idx_verses_order', 'verses', ['title_id', 'order_in_title'])
    op.create_index('idx_comments_title', 'comments', ['title_id'])
    op.create_index('idx_comments_user', 'comments', ['user_id'])
    op.create_index('idx_recordings_title', 'recordings', ['title_id'])
    op.create_index('idx_recordings_user', 'recordings', ['user_id'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_active', 'users', ['is_active'])


def downgrade():
    """Drop all tables"""
    op.drop_index('idx_users_active')
    op.drop_index('idx_users_role')
    op.drop_index('idx_recordings_user')
    op.drop_index('idx_recordings_title')
    op.drop_index('idx_comments_user')
    op.drop_index('idx_comments_title')
    op.drop_index('idx_verses_order')
    op.drop_index('idx_verses_title')
    op.drop_index('idx_titles_order')
    op.drop_index('idx_titles_garden')
    
    op.drop_table('recordings')
    op.drop_table('comments')
    op.drop_table('version_verses')
    op.drop_table('verses')
    op.drop_table('titles')
    op.drop_table('versions')
    op.drop_table('users')