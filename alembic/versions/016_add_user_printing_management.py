"""Add user printing management system

Revision ID: 016
Revises: 015
Create Date: 2025-05-30 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add user printing management system:
    1. Many-to-Many User-Location relationship
    2. Printer management
    3. Location printing configuration
    4. Print job assignment rules
    """
    
    print("Adding user printing management system...")
    
    # ============================================================================
    # 1. CREATE USER-LOCATION MANY-TO-MANY RELATIONSHIP
    # ============================================================================
    
    print("Creating user_locations table...")
    op.create_table(
        'user_locations',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.Integer(), sa.ForeignKey('location.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.Column('can_print', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id', 'location_id'),
        sa.Index('ix_user_locations_user_id', 'user_id'),
        sa.Index('ix_user_locations_location_id', 'location_id')
    )
    
    # ============================================================================
    # 2. CREATE PRINTER MANAGEMENT TABLES
    # ============================================================================
    
    print("Creating printer table...")
    
    # Create printer type enum
    printer_type_enum = sa.Enum(
        'card_printer', 'document_printer', 'photo_printer', 
        'thermal_printer', 'inkjet_printer', 'laser_printer',
        name='printertype'
    )
    printer_type_enum.create(op.get_bind())
    
    # Create printer status enum
    printer_status_enum = sa.Enum(
        'active', 'inactive', 'maintenance', 'offline', 'error',
        name='printerstatus'
    )
    printer_status_enum.create(op.get_bind())
    
    op.create_table(
        'printer',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(100), nullable=False, index=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('printer_type', printer_type_enum, nullable=False),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('manufacturer', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('status', printer_status_enum, nullable=False, default='active', index=True),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('location_id', sa.Integer(), sa.ForeignKey('location.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_maintenance', sa.DateTime(), nullable=True),
        sa.Column('next_maintenance', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True)
    )
    
    # ============================================================================
    # 3. ADD PRINTING CONFIGURATION TO LOCATIONS
    # ============================================================================
    
    print("Adding printing configuration to locations...")
    
    # Create printing type enum
    printing_type_enum = sa.Enum(
        'local', 'centralized', 'hybrid', 'disabled',
        name='printingtype'
    )
    printing_type_enum.create(op.get_bind())
    
    # Add printing configuration columns to location table
    op.add_column('location', sa.Column('printing_enabled', sa.Boolean(), nullable=False, default=True))
    op.add_column('location', sa.Column('printing_type', printing_type_enum, nullable=False, default='local'))
    op.add_column('location', sa.Column('default_print_destination_id', sa.Integer(), sa.ForeignKey('location.id'), nullable=True))
    op.add_column('location', sa.Column('auto_assign_print_jobs', sa.Boolean(), nullable=False, default=True))
    op.add_column('location', sa.Column('max_print_jobs_per_user', sa.Integer(), nullable=False, default=10))
    op.add_column('location', sa.Column('print_job_priority_default', sa.Integer(), nullable=False, default=1))
    
    # ============================================================================
    # 4. ENHANCE PRINT JOB TABLE WITH ASSIGNMENT AND LOCATION TRACKING
    # ============================================================================
    
    print("Enhancing print job table...")
    
    # Add new columns to printjob table
    op.add_column('printjob', sa.Column('auto_assigned', sa.Boolean(), nullable=False, default=False))
    op.add_column('printjob', sa.Column('assignment_rule', sa.String(50), nullable=True))
    op.add_column('printjob', sa.Column('source_location_id', sa.Integer(), sa.ForeignKey('location.id'), nullable=True))
    op.add_column('printjob', sa.Column('target_location_id', sa.Integer(), sa.ForeignKey('location.id'), nullable=True))
    op.add_column('printjob', sa.Column('printer_id', sa.Integer(), sa.ForeignKey('printer.id'), nullable=True))
    
    # ============================================================================
    # 5. MIGRATE EXISTING DATA
    # ============================================================================
    
    print("Migrating existing user-location relationships...")
    
    # Migrate existing single location assignments to many-to-many
    op.execute("""
        INSERT INTO user_locations (user_id, location_id, is_primary, can_print, created_at)
        SELECT 
            id as user_id, 
            location_id, 
            true as is_primary,
            CASE WHEN role = 'PRINTER' THEN true ELSE false END as can_print,
            COALESCE(created_at, NOW()) as created_at
        FROM "user" 
        WHERE location_id IS NOT NULL
    """)
    
    print("✅ User printing management system added successfully!")


def downgrade():
    """
    Remove user printing management system.
    """
    
    print("Removing user printing management system...")
    
    # Remove print job enhancements
    op.drop_column('printjob', 'printer_id')
    op.drop_column('printjob', 'target_location_id')
    op.drop_column('printjob', 'source_location_id')
    op.drop_column('printjob', 'assignment_rule')
    op.drop_column('printjob', 'auto_assigned')
    
    # Remove location printing configuration
    op.drop_column('location', 'print_job_priority_default')
    op.drop_column('location', 'max_print_jobs_per_user')
    op.drop_column('location', 'auto_assign_print_jobs')
    op.drop_column('location', 'default_print_destination_id')
    op.drop_column('location', 'printing_type')
    op.drop_column('location', 'printing_enabled')
    
    # Drop printer table
    op.drop_table('printer')
    
    # Drop user_locations table
    op.drop_table('user_locations')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS printingtype")
    op.execute("DROP TYPE IF EXISTS printerstatus")
    op.execute("DROP TYPE IF EXISTS printertype")
    
    print("✅ User printing management system removed successfully!") 