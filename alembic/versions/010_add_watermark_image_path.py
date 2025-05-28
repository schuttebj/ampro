"""Add watermark_image_path to license model

Revision ID: 010
Revises: 009
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    """Add watermark_image_path column to license table"""
    # Add watermark_image_path field to license table
    op.add_column('license', sa.Column('watermark_image_path', sa.String(), nullable=True))


def downgrade():
    """Remove watermark_image_path column from license table"""
    # Remove watermark_image_path field from license table
    op.drop_column('license', 'watermark_image_path') 