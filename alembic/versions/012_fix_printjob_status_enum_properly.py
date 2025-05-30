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
    
    # Update any existing values to uppercase to match Python enum
    op.execute("""
        UPDATE printjob 
        SET status = CASE 
            WHEN UPPER(status) = 'QUEUED' THEN 'QUEUED'
            WHEN UPPER(status) = 'ASSIGNED' THEN 'ASSIGNED'
            WHEN UPPER(status) = 'PRINTING' THEN 'PRINTING'
            WHEN UPPER(status) = 'COMPLETED' THEN 'COMPLETED'
            WHEN UPPER(status) = 'FAILED' THEN 'FAILED'
            WHEN UPPER(status) = 'CANCELLED' THEN 'CANCELLED'
            ELSE 'QUEUED'
        END
        WHERE status IS NOT NULL;
    """)
    
    # Drop the old enum type if it exists
    op.execute("""
        DROP TYPE IF EXISTS printjobstatus;
    """)
    
    # Create the new enum type with uppercase values to match Python enum
    op.execute("""
        CREATE TYPE printjobstatus AS ENUM ('QUEUED', 'ASSIGNED', 'PRINTING', 'COMPLETED', 'FAILED', 'CANCELLED');
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