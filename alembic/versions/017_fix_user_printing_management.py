"""Fix user printing management system - handle existing enums properly

Revision ID: 017
Revises: 016
Create Date: 2025-05-30 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix user printing management system by properly handling existing enums
    """
    
    print("Fixing user printing management system...")
    
    # Check what already exists and only create what's missing
    connection = op.get_bind()
    
    # ============================================================================
    # 1. CHECK AND CREATE USER-LOCATION TABLE IF NOT EXISTS
    # ============================================================================
    
    # Check if user_locations table exists
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'user_locations'
        );
    """)).scalar()
    
    if not result:
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
    else:
        print("user_locations table already exists")
    
    # ============================================================================
    # 2. CREATE ENUMS IF THEY DON'T EXIST (USING SQLALCHEMY PROPERLY)
    # ============================================================================
    
    # Check and create enums using SQLAlchemy's proper enum handling
    print("Checking and creating enums...")
    
    # Check if printertype enum exists
    enum_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'printertype'
        );
    """)).scalar()
    
    if not enum_exists:
        print("Creating printertype enum...")
        printer_type_enum = postgresql.ENUM(
            'card_printer', 'document_printer', 'photo_printer', 
            'thermal_printer', 'inkjet_printer', 'laser_printer',
            name='printertype'
        )
        printer_type_enum.create(connection)
    
    # Check if printerstatus enum exists
    enum_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'printerstatus'
        );
    """)).scalar()
    
    if not enum_exists:
        print("Creating printerstatus enum...")
        printer_status_enum = postgresql.ENUM(
            'active', 'inactive', 'maintenance', 'offline', 'error',
            name='printerstatus'
        )
        printer_status_enum.create(connection)
    
    # Check if printingtype enum exists
    enum_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'printingtype'
        );
    """)).scalar()
    
    if not enum_exists:
        print("Creating printingtype enum...")
        printing_type_enum = postgresql.ENUM(
            'local', 'centralized', 'hybrid', 'disabled',
            name='printingtype'
        )
        printing_type_enum.create(connection)
    
    # ============================================================================
    # 3. CREATE PRINTER TABLE IF NOT EXISTS
    # ============================================================================
    
    # Check if printer table exists
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'printer'
        );
    """)).scalar()
    
    if not result:
        print("Creating printer table...")
        op.create_table(
            'printer',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('name', sa.String(100), nullable=False, index=True),
            sa.Column('code', sa.String(20), nullable=False, unique=True, index=True),
            sa.Column('printer_type', postgresql.ENUM(name='printertype', create_type=False), nullable=False),
            sa.Column('model', sa.String(100), nullable=True),
            sa.Column('manufacturer', sa.String(100), nullable=True),
            sa.Column('serial_number', sa.String(100), nullable=True),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('status', postgresql.ENUM(name='printerstatus', create_type=False), nullable=False, default='active', index=True),
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
    else:
        print("printer table already exists")
    
    # ============================================================================
    # 4. ADD LOCATION COLUMNS IF THEY DON'T EXIST
    # ============================================================================
    
    print("Adding location printing configuration columns...")
    
    # Check and add columns one by one
    columns_to_add = [
        ('printing_enabled', sa.Boolean(), False, True),
        ('printing_type', postgresql.ENUM(name='printingtype', create_type=False), False, 'local'),
        ('default_print_destination_id', sa.Integer(), True, None),
        ('auto_assign_print_jobs', sa.Boolean(), False, True),
        ('max_print_jobs_per_user', sa.Integer(), False, 10),
        ('print_job_priority_default', sa.Integer(), False, 1),
    ]
    
    for col_name, col_type, nullable, default in columns_to_add:
        # Check if column exists
        result = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'location' AND column_name = '{col_name}'
            );
        """)).scalar()
        
        if not result:
            print(f"Adding column {col_name} to location table...")
            if col_name == 'default_print_destination_id':
                op.add_column('location', sa.Column(col_name, col_type, sa.ForeignKey('location.id'), nullable=nullable))
            else:
                op.add_column('location', sa.Column(col_name, col_type, nullable=nullable, default=default))
    
    # ============================================================================
    # 5. ADD PRINTJOB COLUMNS IF THEY DON'T EXIST
    # ============================================================================
    
    print("Adding printjob enhancement columns...")
    
    printjob_columns = [
        ('auto_assigned', sa.Boolean(), False, False),
        ('assignment_rule', sa.String(50), True, None),
        ('source_location_id', sa.Integer(), True, None),
        ('target_location_id', sa.Integer(), True, None),
        ('printer_id', sa.Integer(), True, None),
    ]
    
    for col_name, col_type, nullable, default in printjob_columns:
        # Check if column exists
        result = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'printjob' AND column_name = '{col_name}'
            );
        """)).scalar()
        
        if not result:
            print(f"Adding column {col_name} to printjob table...")
            if col_name in ['source_location_id', 'target_location_id']:
                op.add_column('printjob', sa.Column(col_name, col_type, sa.ForeignKey('location.id'), nullable=nullable))
            elif col_name == 'printer_id':
                op.add_column('printjob', sa.Column(col_name, col_type, sa.ForeignKey('printer.id'), nullable=nullable))
            else:
                op.add_column('printjob', sa.Column(col_name, col_type, nullable=nullable, default=default))
    
    # ============================================================================
    # 6. MIGRATE EXISTING DATA IF NOT ALREADY DONE
    # ============================================================================
    
    print("Checking if data migration is needed...")
    
    # Check if we have any data in user_locations
    result = connection.execute(sa.text("SELECT COUNT(*) FROM user_locations;")).scalar()
    
    if result == 0:
        print("Migrating existing user-location relationships...")
        # Migrate existing single location assignments to many-to-many
        connection.execute(sa.text("""
            INSERT INTO user_locations (user_id, location_id, is_primary, can_print, created_at)
            SELECT 
                id as user_id, 
                location_id, 
                true as is_primary,
                CASE WHEN role = 'PRINTER' THEN true ELSE false END as can_print,
                COALESCE(created_at, NOW()) as created_at
            FROM "user" 
            WHERE location_id IS NOT NULL
            ON CONFLICT (user_id, location_id) DO NOTHING
        """))
    else:
        print("Data migration already completed")
    
    print("✅ User printing management system fixed successfully!")


def downgrade():
    """
    Remove user printing management system enhancements
    """
    
    print("Removing user printing management system...")
    
    # Remove printjob columns
    printjob_columns = ['printer_id', 'target_location_id', 'source_location_id', 'assignment_rule', 'auto_assigned']
    for col in printjob_columns:
        try:
            op.drop_column('printjob', col)
        except:
            pass
    
    # Remove location columns
    location_columns = ['print_job_priority_default', 'max_print_jobs_per_user', 'auto_assign_print_jobs', 
                       'default_print_destination_id', 'printing_type', 'printing_enabled']
    for col in location_columns:
        try:
            op.drop_column('location', col)
        except:
            pass
    
    # Drop tables
    try:
        op.drop_table('printer')
    except:
        pass
    
    try:
        op.drop_table('user_locations')
    except:
        pass
    
    print("✅ User printing management system removed!") 