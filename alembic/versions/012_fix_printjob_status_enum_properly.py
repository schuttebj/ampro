"""Fix PrintJobStatus enum properly

Revision ID: 012
Revises: 010
Create Date: 2024-01-20 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    """
    Properly fix PrintJobStatus enum values by converting to text first.
    """
    
    # Simple and safe approach - convert column to text, update values, recreate enum
    op.execute("""
        -- Convert status column to text first to avoid enum casting issues
        ALTER TABLE printjob ALTER COLUMN status TYPE text;
    """)
    
    # Update any existing values to lowercase
    op.execute("""
        UPDATE printjob 
        SET status = CASE 
            WHEN UPPER(status) = 'QUEUED' THEN 'queued'
            WHEN UPPER(status) = 'ASSIGNED' THEN 'assigned'
            WHEN UPPER(status) = 'PRINTING' THEN 'printing'
            WHEN UPPER(status) = 'COMPLETED' THEN 'completed'
            WHEN UPPER(status) = 'FAILED' THEN 'failed'
            WHEN UPPER(status) = 'CANCELLED' THEN 'cancelled'
            ELSE 'queued'
        END
        WHERE status IS NOT NULL;
    """)
    
    # Drop the old enum type if it exists
    op.execute("""
        DROP TYPE IF EXISTS printjobstatus;
    """)
    
    # Create the new enum type
    op.execute("""
        CREATE TYPE printjobstatus AS ENUM ('queued', 'assigned', 'printing', 'completed', 'failed', 'cancelled');
    """)
    
    # Convert the column back to enum type
    op.execute("""
        ALTER TABLE printjob ALTER COLUMN status TYPE printjobstatus USING status::printjobstatus;
    """)


def downgrade():
    """
    Revert to text column
    """
    op.execute("""
        ALTER TABLE printjob ALTER COLUMN status TYPE text;
        DROP TYPE IF EXISTS printjobstatus;
    """) 