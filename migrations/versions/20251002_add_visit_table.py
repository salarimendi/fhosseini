"""
ایجاد جدول visits برای آمار بازدید روزانه
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'visits',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.String(length=10), nullable=False, unique=True),
        sa.Column('count', sa.Integer(), nullable=False, default=0)
    )

def downgrade():
    op.drop_table('visits')
