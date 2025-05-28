"""Add workflow tables and user roles

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Update ApplicationStatus enum to include new statuses
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'pending_payment'")
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'license_generated'")
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'queued_for_printing'")
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'printing'")
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'printed'")
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'shipped'")
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'ready_for_collection'")
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'cancelled'")
    
    # Update LicenseStatus enum to include new statuses
    op.execute("ALTER TYPE licensestatus ADD VALUE IF NOT EXISTS 'pending_collection'")
    
    # Create PrintJobStatus enum - check existence first
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'printjobstatus') THEN
                CREATE TYPE printjobstatus AS ENUM ('queued', 'assigned', 'printing', 'completed', 'failed', 'cancelled');
            END IF;
        END
        $$;
    """)
    
    # Create ShippingStatus enum - check existence first  
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'shippingstatus') THEN
                CREATE TYPE shippingstatus AS ENUM ('pending', 'in_transit', 'delivered', 'failed');
            END IF;
        END
        $$;
    """)
    
    # Create UserRole enum - check existence first
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                CREATE TYPE userrole AS ENUM ('admin', 'manager', 'officer', 'printer', 'viewer');
            END IF;
        END
        $$;
    """)
    
    # Add role column to user table
    op.add_column('user', sa.Column('role', postgresql.ENUM('admin', 'manager', 'officer', 'printer', 'viewer', name='userrole'), nullable=False, server_default='officer'))
    
    # Update existing superusers to admin role
    op.execute("UPDATE \"user\" SET role = 'admin' WHERE is_superuser = true")
    
    # Add new columns to license table
    op.add_column('license', sa.Column('collection_point', sa.String(), nullable=True))
    op.add_column('license', sa.Column('collected_at', sa.DateTime(), nullable=True))
    op.add_column('license', sa.Column('collected_by_user_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint for collected_by_user_id
    op.create_foreign_key(
        'fk_license_collected_by_user',
        'license', 'user',
        ['collected_by_user_id'], ['id']
    )
    
    # Add new columns to licenseapplication table
    op.add_column('licenseapplication', sa.Column('payment_amount', sa.Integer(), nullable=True))
    op.add_column('licenseapplication', sa.Column('payment_reference', sa.String(), nullable=True))
    op.add_column('licenseapplication', sa.Column('collection_point', sa.String(), nullable=True))
    op.add_column('licenseapplication', sa.Column('preferred_collection_date', sa.Date(), nullable=True))
    
    # Create printjob table
    op.create_table('printjob',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('license_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('queued', 'assigned', 'printing', 'completed', 'failed', 'cancelled', name='printjobstatus'), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('front_pdf_path', sa.String(), nullable=False),
        sa.Column('back_pdf_path', sa.String(), nullable=False),
        sa.Column('combined_pdf_path', sa.String(), nullable=True),
        sa.Column('queued_at', sa.DateTime(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
        sa.Column('printed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('printer_name', sa.String(), nullable=True),
        sa.Column('copies_printed', sa.Integer(), nullable=False),
        sa.Column('print_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['licenseapplication.id'], ),
        sa.ForeignKeyConstraint(['license_id'], ['license.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['printed_by_user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_printjob_id'), 'printjob', ['id'], unique=False)
    
    # Create shippingrecord table
    op.create_table('shippingrecord',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('license_id', sa.Integer(), nullable=False),
        sa.Column('print_job_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'in_transit', 'delivered', 'failed', name='shippingstatus'), nullable=False),
        sa.Column('tracking_number', sa.String(), nullable=True),
        sa.Column('collection_point', sa.String(), nullable=False),
        sa.Column('collection_address', sa.Text(), nullable=True),
        sa.Column('shipped_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('shipped_by_user_id', sa.Integer(), nullable=True),
        sa.Column('received_by_user_id', sa.Integer(), nullable=True),
        sa.Column('shipping_method', sa.String(), nullable=True),
        sa.Column('shipping_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['licenseapplication.id'], ),
        sa.ForeignKeyConstraint(['license_id'], ['license.id'], ),
        sa.ForeignKeyConstraint(['print_job_id'], ['printjob.id'], ),
        sa.ForeignKeyConstraint(['shipped_by_user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['received_by_user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shippingrecord_id'), 'shippingrecord', ['id'], unique=False)
    op.create_index(op.f('ix_shippingrecord_tracking_number'), 'shippingrecord', ['tracking_number'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_shippingrecord_tracking_number'), table_name='shippingrecord')
    op.drop_index(op.f('ix_shippingrecord_id'), table_name='shippingrecord')
    op.drop_table('shippingrecord')
    
    op.drop_index(op.f('ix_printjob_id'), table_name='printjob')
    op.drop_table('printjob')
    
    # Remove new columns from licenseapplication
    op.drop_column('licenseapplication', 'preferred_collection_date')
    op.drop_column('licenseapplication', 'collection_point')
    op.drop_column('licenseapplication', 'payment_reference')
    op.drop_column('licenseapplication', 'payment_amount')
    
    # Remove foreign key and columns from license
    op.drop_constraint('fk_license_collected_by_user', 'license', type_='foreignkey')
    op.drop_column('license', 'collected_by_user_id')
    op.drop_column('license', 'collected_at')
    op.drop_column('license', 'collection_point')
    
    # Remove role column
    op.drop_column('user', 'role')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS shippingstatus")
    op.execute("DROP TYPE IF EXISTS printjobstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
    
    # Note: Cannot easily remove enum values in PostgreSQL, so we leave them 