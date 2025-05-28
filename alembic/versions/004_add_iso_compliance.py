"""Add ISO 18013 compliance fields to license table

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add ISO 18013 compliance fields to license table
    op.add_column('license', sa.Column('iso_country_code', sa.String(3), nullable=False, server_default='ZAF'))
    op.add_column('license', sa.Column('iso_issuing_authority', sa.String(100), nullable=False, server_default='Department of Transport'))
    op.add_column('license', sa.Column('iso_document_number', sa.String(50), nullable=True))
    op.add_column('license', sa.Column('iso_version', sa.String(10), nullable=False, server_default='18013-1:2018'))
    
    # Add biometric and security fields
    op.add_column('license', sa.Column('biometric_template', sa.Text(), nullable=True))
    op.add_column('license', sa.Column('digital_signature', sa.Text(), nullable=True))
    op.add_column('license', sa.Column('security_features', sa.Text(), nullable=True))
    
    # Add Machine Readable Zone (MRZ) fields
    op.add_column('license', sa.Column('mrz_line1', sa.String(44), nullable=True))
    op.add_column('license', sa.Column('mrz_line2', sa.String(44), nullable=True))
    op.add_column('license', sa.Column('mrz_line3', sa.String(44), nullable=True))
    
    # Add RFID/Chip fields
    op.add_column('license', sa.Column('chip_serial_number', sa.String(50), nullable=True))
    op.add_column('license', sa.Column('chip_data_encrypted', sa.Text(), nullable=True))
    
    # Add international recognition fields
    op.add_column('license', sa.Column('international_validity', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('license', sa.Column('vienna_convention_compliant', sa.Boolean(), nullable=False, server_default='true'))
    
    # Add watermark PDF path
    op.add_column('license', sa.Column('watermark_pdf_path', sa.String(), nullable=True))
    
    # Create indexes for performance
    op.create_index('ix_license_iso_country_code', 'license', ['iso_country_code'])
    op.create_index('ix_license_chip_serial_number', 'license', ['chip_serial_number'])
    op.create_index('ix_license_iso_document_number', 'license', ['iso_document_number'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_license_iso_document_number', table_name='license')
    op.drop_index('ix_license_chip_serial_number', table_name='license')
    op.drop_index('ix_license_iso_country_code', table_name='license')
    
    # Remove ISO compliance columns
    op.drop_column('license', 'watermark_pdf_path')
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