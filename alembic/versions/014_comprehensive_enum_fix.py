"""Comprehensive enum fix for all status fields

Revision ID: 014
Revises: 013
Create Date: 2025-05-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    """
    Comprehensive fix for all enum inconsistencies.
    This migration ensures all enum values match Python definitions.
    """
    
    # ============================================================================
    # Fix PrintJobStatus enum (most critical - this is causing the current error)
    # ============================================================================
    
    print("Fixing PrintJobStatus enum...")
    
    # Step 1: Convert status column to text to avoid enum constraints
    op.execute("""
        ALTER TABLE printjob ALTER COLUMN status TYPE text;
    """)
    
    # Step 2: Update all existing lowercase values to uppercase to match Python enum
    op.execute("""
        UPDATE printjob 
        SET status = CASE 
            WHEN LOWER(status) = 'queued' THEN 'QUEUED'
            WHEN LOWER(status) = 'assigned' THEN 'ASSIGNED'
            WHEN LOWER(status) = 'printing' THEN 'PRINTING'
            WHEN LOWER(status) = 'completed' THEN 'COMPLETED'
            WHEN LOWER(status) = 'failed' THEN 'FAILED'
            WHEN LOWER(status) = 'cancelled' THEN 'CANCELLED'
            WHEN status = 'QUEUED' THEN 'QUEUED'  -- Already correct
            WHEN status = 'ASSIGNED' THEN 'ASSIGNED'
            WHEN status = 'PRINTING' THEN 'PRINTING'
            WHEN status = 'COMPLETED' THEN 'COMPLETED'
            WHEN status = 'FAILED' THEN 'FAILED'
            WHEN status = 'CANCELLED' THEN 'CANCELLED'
            ELSE 'QUEUED'  -- Default fallback
        END
        WHERE status IS NOT NULL;
    """)
    
    # Step 3: Drop and recreate the enum type with correct values
    op.execute("""
        DROP TYPE IF EXISTS printjobstatus CASCADE;
    """)
    
    op.execute("""
        CREATE TYPE printjobstatus AS ENUM (
            'QUEUED', 
            'ASSIGNED', 
            'PRINTING', 
            'COMPLETED', 
            'FAILED', 
            'CANCELLED'
        );
    """)
    
    # Step 4: Convert column back to enum type
    op.execute("""
        ALTER TABLE printjob 
        ALTER COLUMN status TYPE printjobstatus 
        USING status::printjobstatus;
    """)
    
    # Step 5: Set proper default value
    op.execute("""
        ALTER TABLE printjob 
        ALTER COLUMN status SET DEFAULT 'QUEUED'::printjobstatus;
    """)
    
    # ============================================================================
    # Verify the fix worked
    # ============================================================================
    
    # Show current status distribution
    print("PrintJob status distribution after fix:")
    result = op.get_bind().execute(sa.text("""
        SELECT status, COUNT(*) as count 
        FROM printjob 
        GROUP BY status 
        ORDER BY status;
    """))
    
    for row in result:
        print(f"  {row[0]}: {row[1]} records")
    
    print("PrintJobStatus enum fix completed successfully!")


def downgrade():
    """
    Revert to previous state (not recommended in production)
    """
    # Convert back to text
    op.execute("""
        ALTER TABLE printjob ALTER COLUMN status TYPE text;
    """)
    
    # Drop the enum type
    op.execute("""
        DROP TYPE IF EXISTS printjobstatus CASCADE;
    """) 