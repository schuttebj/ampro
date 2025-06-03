"""add_hardware_management_system

Revision ID: 020
Revises: 019
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade():
    # Check and create the hardware type enum only if it doesn't exist
    connection = op.get_bind()
    
    # Check if hardwaretype enum exists
    enum_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'hardwaretype'
        );
    """)).scalar()
    
    if not enum_exists:
        hardwaretype_enum = postgresql.ENUM(
            'WEBCAM', 'SECURITY_CAMERA', 'FINGERPRINT_SCANNER', 'IRIS_SCANNER', 
            'FACE_RECOGNITION', 'CARD_READER', 'SIGNATURE_PAD', 'DOCUMENT_SCANNER', 
            'BARCODE_SCANNER', 'THERMAL_SENSOR', 'OTHER',
            name='hardwaretype'
        )
        hardwaretype_enum.create(op.get_bind())
    
    # Check if hardwarestatus enum exists
    enum_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'hardwarestatus'
        );
    """)).scalar()
    
    if not enum_exists:
        hardwarestatus_enum = postgresql.ENUM(
            'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'OFFLINE', 'ERROR', 'CALIBRATING',
            name='hardwarestatus'
        )
        hardwarestatus_enum.create(op.get_bind())
    
    # Check if hardware table exists before creating it
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'hardware'
        );
    """)).scalar()
    
    if not table_exists:
        # Create hardware table
        op.create_table(
            'hardware',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('code', sa.String(length=20), nullable=False),
            sa.Column('hardware_type', postgresql.ENUM(name='hardwaretype', create_type=False), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=True),
            sa.Column('manufacturer', sa.String(length=100), nullable=True),
            sa.Column('serial_number', sa.String(length=100), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('usb_port', sa.String(length=20), nullable=True),
            sa.Column('device_id', sa.String(length=100), nullable=True),
            sa.Column('status', postgresql.ENUM(name='hardwarestatus', create_type=False), nullable=False),
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
        
        # Create indexes only if table was created
        op.create_index(op.f('ix_hardware_name'), 'hardware', ['name'], unique=False)
        op.create_index(op.f('ix_hardware_code'), 'hardware', ['code'], unique=True)
        op.create_index(op.f('ix_hardware_status'), 'hardware', ['status'], unique=False)
        op.create_index(op.f('ix_hardware_location_id'), 'hardware', ['location_id'], unique=False)


def downgrade():
    # Check if hardware table exists before dropping
    connection = op.get_bind()
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'hardware'
        );
    """)).scalar()
    
    if table_exists:
        # Drop indexes
        op.drop_index(op.f('ix_hardware_location_id'), table_name='hardware')
        op.drop_index(op.f('ix_hardware_status'), table_name='hardware')
        op.drop_index(op.f('ix_hardware_code'), table_name='hardware')
        op.drop_index(op.f('ix_hardware_name'), table_name='hardware')
        
        # Drop hardware table
        op.drop_table('hardware')
    
    # Drop enums if they exist
    op.execute('DROP TYPE IF EXISTS hardwarestatus')
    op.execute('DROP TYPE IF EXISTS hardwaretype') 