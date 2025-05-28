"""Add file management fields

Revision ID: 002
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '002'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Get connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if license table exists
    if 'license' in inspector.get_table_names():
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('license')]
        
        # Add file management fields to license table only if they don't exist
        license_columns = [
            ('front_image_path', sa.String(), True),
            ('back_image_path', sa.String(), True),
            ('front_pdf_path', sa.String(), True),
            ('back_pdf_path', sa.String(), True),
            ('combined_pdf_path', sa.String(), True),
            ('original_photo_path', sa.String(), True),
            ('processed_photo_path', sa.String(), True),
            ('photo_last_updated', sa.DateTime(), True),
            ('last_generated', sa.DateTime(), True),
            ('generation_version', sa.String(), False, '1.0'),
        ]
        
        for col_name, col_type, nullable, *default in license_columns:
            if col_name not in existing_columns:
                if default:
                    op.add_column('license', sa.Column(col_name, col_type, nullable=nullable, server_default=default[0]))
                else:
                    op.add_column('license', sa.Column(col_name, col_type, nullable=nullable))
    
    # Check if citizen table exists
    if 'citizen' in inspector.get_table_names():
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('citizen')]
        
        # Add photo management fields to citizen table only if they don't exist
        citizen_columns = [
            ('stored_photo_path', sa.String(), True),
            ('processed_photo_path', sa.String(), True),
            ('photo_uploaded_at', sa.DateTime(), True),
            ('photo_processed_at', sa.DateTime(), True),
        ]
        
        for col_name, col_type, nullable in citizen_columns:
            if col_name not in existing_columns:
                op.add_column('citizen', sa.Column(col_name, col_type, nullable=nullable))


def downgrade():
    # Get connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Remove fields from citizen table if they exist
    if 'citizen' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('citizen')]
        
        citizen_columns_to_remove = [
            'photo_processed_at',
            'photo_uploaded_at', 
            'processed_photo_path',
            'stored_photo_path'
        ]
        
        for col_name in citizen_columns_to_remove:
            if col_name in existing_columns:
                op.drop_column('citizen', col_name)
    
    # Remove fields from license table if they exist
    if 'license' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('license')]
        
        license_columns_to_remove = [
            'generation_version',
            'last_generated',
            'photo_last_updated',
            'processed_photo_path',
            'original_photo_path',
            'combined_pdf_path',
            'back_pdf_path',
            'front_pdf_path',
            'back_image_path',
            'front_image_path'
        ]
        
        for col_name in license_columns_to_remove:
            if col_name in existing_columns:
                op.drop_column('license', col_name) 