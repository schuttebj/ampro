"""Add file management fields

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add file management fields to license table
    op.add_column('license', sa.Column('front_image_path', sa.String(), nullable=True))
    op.add_column('license', sa.Column('back_image_path', sa.String(), nullable=True))
    op.add_column('license', sa.Column('front_pdf_path', sa.String(), nullable=True))
    op.add_column('license', sa.Column('back_pdf_path', sa.String(), nullable=True))
    op.add_column('license', sa.Column('combined_pdf_path', sa.String(), nullable=True))
    op.add_column('license', sa.Column('original_photo_path', sa.String(), nullable=True))
    op.add_column('license', sa.Column('processed_photo_path', sa.String(), nullable=True))
    op.add_column('license', sa.Column('photo_last_updated', sa.DateTime(), nullable=True))
    op.add_column('license', sa.Column('last_generated', sa.DateTime(), nullable=True))
    op.add_column('license', sa.Column('generation_version', sa.String(), nullable=False, server_default='1.0'))
    
    # Add photo management fields to citizen table
    op.add_column('citizen', sa.Column('stored_photo_path', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('processed_photo_path', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('photo_uploaded_at', sa.DateTime(), nullable=True))
    op.add_column('citizen', sa.Column('photo_processed_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove fields from citizen table
    op.drop_column('citizen', 'photo_processed_at')
    op.drop_column('citizen', 'photo_uploaded_at')
    op.drop_column('citizen', 'processed_photo_path')
    op.drop_column('citizen', 'stored_photo_path')
    
    # Remove fields from license table
    op.drop_column('license', 'generation_version')
    op.drop_column('license', 'last_generated')
    op.drop_column('license', 'photo_last_updated')
    op.drop_column('license', 'processed_photo_path')
    op.drop_column('license', 'original_photo_path')
    op.drop_column('license', 'combined_pdf_path')
    op.drop_column('license', 'back_pdf_path')
    op.drop_column('license', 'front_pdf_path')
    op.drop_column('license', 'back_image_path')
    op.drop_column('license', 'front_image_path') 