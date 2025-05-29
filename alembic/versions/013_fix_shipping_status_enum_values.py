"""Fix ShippingStatus enum values

Revision ID: 013
Revises: 012
Create Date: 2025-05-29 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix ShippingStatus enum values by converting to text first.
    """
    
    # Check if shippingrecord table exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'shippingrecord') THEN
                -- Convert status column to text first to avoid enum casting issues
                ALTER TABLE shippingrecord ALTER COLUMN status TYPE text;
                
                -- Update any existing values to lowercase
                UPDATE shippingrecord 
                SET status = CASE 
                    WHEN UPPER(status) = 'PENDING' THEN 'pending'
                    WHEN UPPER(status) = 'IN_TRANSIT' THEN 'in_transit'
                    WHEN UPPER(status) = 'DELIVERED' THEN 'delivered'
                    WHEN UPPER(status) = 'FAILED' THEN 'failed'
                    ELSE 'pending'
                END
                WHERE status IS NOT NULL;
            END IF;
        END
        $$;
    """)
    
    # Drop the old enum type if it exists
    op.execute("""
        DROP TYPE IF EXISTS shippingstatus;
    """)
    
    # Create the new enum type
    op.execute("""
        CREATE TYPE shippingstatus AS ENUM ('pending', 'in_transit', 'delivered', 'failed');
    """)
    
    # Convert the column back to enum type if table exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'shippingrecord') THEN
                ALTER TABLE shippingrecord ALTER COLUMN status TYPE shippingstatus USING status::shippingstatus;
            END IF;
        END
        $$;
    """)


def downgrade():
    """
    Revert to text column
    """
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'shippingrecord') THEN
                ALTER TABLE shippingrecord ALTER COLUMN status TYPE text;
            END IF;
        END
        $$;
        DROP TYPE IF EXISTS shippingstatus;
    """) 