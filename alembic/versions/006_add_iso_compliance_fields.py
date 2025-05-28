"""Add ISO compliance fields to license table

Revision ID: 006_add_iso_compliance_fields
Revises: 005
Create Date: 2025-01-28 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_iso_compliance_fields'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Add ISO 18013 compliance fields to license table."""
    
    # Add ISO compliance fields
    op.add_column('license', sa.Column('iso_country_code', sa.String(3), nullable=False, server_default='ZAF'))
    op.add_column('license', sa.Column('iso_issuing_authority', sa.String(100), nullable=False, server_default='Department of Transport'))
    op.add_column('license', sa.Column('iso_document_number', sa.String(50), nullable=True))
    op.add_column('license', sa.Column('iso_version', sa.String(20), nullable=False, server_default='18013-1:2018'))
    
    # Add biometric and security fields
    op.add_column('license', sa.Column('biometric_template', sa.Text, nullable=True))
    op.add_column('license', sa.Column('digital_signature', sa.Text, nullable=True))
    op.add_column('license', sa.Column('security_features', sa.Text, nullable=True))
    
    # Add Machine Readable Zone (MRZ) fields
    op.add_column('license', sa.Column('mrz_line1', sa.String(44), nullable=True))
    op.add_column('license', sa.Column('mrz_line2', sa.String(44), nullable=True))
    op.add_column('license', sa.Column('mrz_line3', sa.String(44), nullable=True))
    
    # Add RFID/Chip fields
    op.add_column('license', sa.Column('chip_serial_number', sa.String(50), nullable=True))
    op.add_column('license', sa.Column('chip_data_encrypted', sa.Text, nullable=True))
    
    # Add international recognition fields
    op.add_column('license', sa.Column('international_validity', sa.Boolean, nullable=False, server_default='true'))
    op.add_column('license', sa.Column('vienna_convention_compliant', sa.Boolean, nullable=False, server_default='true'))
    
    # Add file storage fields
    op.add_column('license', sa.Column('front_image_path', sa.String, nullable=True))
    op.add_column('license', sa.Column('back_image_path', sa.String, nullable=True))
    op.add_column('license', sa.Column('front_pdf_path', sa.String, nullable=True))
    op.add_column('license', sa.Column('back_pdf_path', sa.String, nullable=True))
    op.add_column('license', sa.Column('combined_pdf_path', sa.String, nullable=True))
    op.add_column('license', sa.Column('watermark_pdf_path', sa.String, nullable=True))
    
    # Add photo tracking fields
    op.add_column('license', sa.Column('original_photo_path', sa.String, nullable=True))
    op.add_column('license', sa.Column('processed_photo_path', sa.String, nullable=True))
    op.add_column('license', sa.Column('photo_last_updated', sa.DateTime, nullable=True))
    
    # Add generation metadata fields
    op.add_column('license', sa.Column('last_generated', sa.DateTime, nullable=True))
    op.add_column('license', sa.Column('generation_version', sa.String, nullable=False, server_default='1.0'))
    
    # Add collection tracking fields
    op.add_column('license', sa.Column('collection_point', sa.String, nullable=True))
    op.add_column('license', sa.Column('collected_at', sa.DateTime, nullable=True))
    op.add_column('license', sa.Column('collected_by_user_id', sa.Integer, nullable=True))
    
    # Add foreign key constraint for collected_by_user_id
    op.create_foreign_key(
        'fk_license_collected_by_user_id',
        'license', 'user',
        ['collected_by_user_id'], ['id']
    )


def downgrade():
    """Remove ISO compliance fields from license table."""
    
    # Drop foreign key constraint first
    op.drop_constraint('fk_license_collected_by_user_id', 'license', type_='foreignkey')
    
    # Drop all added columns
    op.drop_column('license', 'collected_by_user_id')
    op.drop_column('license', 'collected_at')
    op.drop_column('license', 'collection_point')
    op.drop_column('license', 'generation_version')
    op.drop_column('license', 'last_generated')
    op.drop_column('license', 'photo_last_updated')
    op.drop_column('license', 'processed_photo_path')
    op.drop_column('license', 'original_photo_path')
    op.drop_column('license', 'watermark_pdf_path')
    op.drop_column('license', 'combined_pdf_path')
    op.drop_column('license', 'back_pdf_path')
    op.drop_column('license', 'front_pdf_path')
    op.drop_column('license', 'back_image_path')
    op.drop_column('license', 'front_image_path')
    op.drop_column('license', 'vienna_convention_compliant')
    op.drop_column('license', 'international_validity')
    op.drop_column('license', 'chip_data_encrypted')
    op.drop_column('license', 'chip_serial_number')
    op.drop_column('license', 'mrz_line3')
    op.drop_column('license', 'mrz_line2')
    op.drop_column('license', 'mrz_line1')
    op.drop_column('license', 'security_features')
    op.drop_column('license', 'digital_signature')
    op.drop_column('license', 'biometric_template')
    op.drop_column('license', 'iso_version')
    op.drop_column('license', 'iso_document_number')
    op.drop_column('license', 'iso_issuing_authority')
    op.drop_column('license', 'iso_country_code') 