"""add_hardware_management_system

Revision ID: 020_add_hardware_management_system
Revises: 019_fix_printing_type_to_uppercase
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '020_add_hardware_management_system'
down_revision = '019_fix_printing_type_to_uppercase'
branch_labels = None
depends_on = None


def upgrade():
    # Create the hardware type enum
    hardwaretype_enum = postgresql.ENUM(
        'WEBCAM', 'SECURITY_CAMERA', 'FINGERPRINT_SCANNER', 'IRIS_SCANNER', 
        'FACE_RECOGNITION', 'CARD_READER', 'SIGNATURE_PAD', 'DOCUMENT_SCANNER', 
        'BARCODE_SCANNER', 'THERMAL_SENSOR', 'OTHER',
        name='hardwaretype'
    )
    hardwaretype_enum.create(op.get_bind())
    
    # Create the hardware status enum
    hardwarestatus_enum = postgresql.ENUM(
        'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'OFFLINE', 'ERROR', 'CALIBRATING',
        name='hardwarestatus'
    )
    hardwarestatus_enum.create(op.get_bind())
    
    # Create hardware table
    op.create_table(
        'hardware',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('hardware_type', hardwaretype_enum, nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('manufacturer', sa.String(length=100), nullable=True),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('usb_port', sa.String(length=20), nullable=True),
        sa.Column('device_id', sa.String(length=100), nullable=True),
        sa.Column('status', hardwarestatus_enum, nullable=False),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('driver_info', sa.JSON(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_maintenance', sa.DateTime(), nullable=True),
        sa.Column('next_maintenance', sa.DateTime(), nullable=True),
        sa.Column('last_online', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['location.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # Create indexes
    op.create_index(op.f('ix_hardware_name'), 'hardware', ['name'], unique=False)
    op.create_index(op.f('ix_hardware_code'), 'hardware', ['code'], unique=True)
    op.create_index(op.f('ix_hardware_status'), 'hardware', ['status'], unique=False)
    op.create_index(op.f('ix_hardware_location_id'), 'hardware', ['location_id'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_hardware_location_id'), table_name='hardware')
    op.drop_index(op.f('ix_hardware_status'), table_name='hardware')
    op.drop_index(op.f('ix_hardware_code'), table_name='hardware')
    op.drop_index(op.f('ix_hardware_name'), table_name='hardware')
    
    # Drop hardware table
    op.drop_table('hardware')
    
    # Drop enums
    op.execute('DROP TYPE hardwarestatus')
    op.execute('DROP TYPE hardwaretype') 