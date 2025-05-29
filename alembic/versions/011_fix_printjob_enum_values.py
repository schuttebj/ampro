"""Fix PrintJobStatus enum values

Revision ID: 011
Revises: 010
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix PrintJobStatus enum values to ensure they match the model definition.
    """
    
    # Check if the enum exists and what values it has
    op.execute("""
        DO $$
        BEGIN
            -- Check if enum exists with wrong values and recreate if needed
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'printjobstatus') THEN
                -- Drop and recreate the enum type with correct values
                -- First, we need to create a new temporary type
                CREATE TYPE printjobstatus_new AS ENUM ('queued', 'assigned', 'printing', 'completed', 'failed', 'cancelled');
                
                -- Update the table to use the new type (converting any existing data)
                ALTER TABLE printjob ALTER COLUMN status TYPE printjobstatus_new 
                USING CASE 
                    WHEN status::text = 'QUEUED' THEN 'queued'::printjobstatus_new
                    WHEN status::text = 'ASSIGNED' THEN 'assigned'::printjobstatus_new
                    WHEN status::text = 'PRINTING' THEN 'printing'::printjobstatus_new
                    WHEN status::text = 'COMPLETED' THEN 'completed'::printjobstatus_new
                    WHEN status::text = 'FAILED' THEN 'failed'::printjobstatus_new
                    WHEN status::text = 'CANCELLED' THEN 'cancelled'::printjobstatus_new
                    ELSE status::printjobstatus_new
                END;
                
                -- Drop the old type and rename the new one
                DROP TYPE printjobstatus;
                ALTER TYPE printjobstatus_new RENAME TO printjobstatus;
            ELSE
                -- Create the enum if it doesn't exist
                CREATE TYPE printjobstatus AS ENUM ('queued', 'assigned', 'printing', 'completed', 'failed', 'cancelled');
                
                -- Update the column to use the enum type
                ALTER TABLE printjob ALTER COLUMN status TYPE printjobstatus USING status::printjobstatus;
            END IF;
        END
        $$;
    """)
    
    # Ensure any existing print jobs have valid enum values
    op.execute("""
        UPDATE printjob 
        SET status = 'queued' 
        WHERE status::text NOT IN ('queued', 'assigned', 'printing', 'completed', 'failed', 'cancelled');
    """)


def downgrade():
    """
    Revert the enum changes
    """
    # This downgrade just ensures the enum exists, doesn't change values
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'printjobstatus') THEN
                CREATE TYPE printjobstatus AS ENUM ('queued', 'assigned', 'printing', 'completed', 'failed', 'cancelled');
                ALTER TABLE printjob ALTER COLUMN status TYPE printjobstatus USING status::printjobstatus;
            END IF;
        END
        $$;
    """) 