"""Fix ShippingStatus enum to match Python definitions

Revision ID: 015
Revises: 014
Create Date: 2025-05-30 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix ShippingStatus enum to match Python enum values.
    Python enum uses lowercase values, so we need to update database to match.
    """
    
    print("Fixing ShippingStatus enum...")
    
    # Check if shippingrecord table exists first
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'shippingrecord') THEN
                -- Step 1: Convert status column to text to avoid enum constraints
                ALTER TABLE shippingrecord ALTER COLUMN status TYPE text;
                
                -- Step 2: Update uppercase values to lowercase to match Python enum
                UPDATE shippingrecord 
                SET status = CASE 
                    WHEN UPPER(status) = 'PENDING' THEN 'pending'
                    WHEN UPPER(status) = 'IN_TRANSIT' THEN 'in_transit'
                    WHEN UPPER(status) = 'DELIVERED' THEN 'delivered'
                    WHEN UPPER(status) = 'FAILED' THEN 'failed'
                    WHEN LOWER(status) = 'pending' THEN 'pending'  -- Already correct
                    WHEN LOWER(status) = 'in_transit' THEN 'in_transit'
                    WHEN LOWER(status) = 'delivered' THEN 'delivered'
                    WHEN LOWER(status) = 'failed' THEN 'failed'
                    ELSE 'pending'  -- Default fallback
                END
                WHERE status IS NOT NULL;
            END IF;
        END
        $$;
    """)
    
    # Step 3: Drop and recreate the enum type with correct lowercase values
    op.execute("""
        DROP TYPE IF EXISTS shippingstatus CASCADE;
    """)
    
    op.execute("""
        CREATE TYPE shippingstatus AS ENUM (
            'pending',
            'in_transit', 
            'delivered',
            'failed'
        );
    """)
    
    # Step 4: Convert column back to enum type if table exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'shippingrecord') THEN
                ALTER TABLE shippingrecord 
                ALTER COLUMN status TYPE shippingstatus 
                USING status::shippingstatus;
                
                -- Set proper default value
                ALTER TABLE shippingrecord 
                ALTER COLUMN status SET DEFAULT 'pending'::shippingstatus;
            END IF;
        END
        $$;
    """)
    
    # Step 5: Show current status distribution
    print("ShippingRecord status distribution after fix:")
    try:
        result = op.get_bind().execute(sa.text("""
            SELECT 
                CASE 
                    WHEN EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'shippingrecord')
                    THEN (
                        SELECT string_agg(status || ': ' || count::text, ', ' ORDER BY status) 
                        FROM (
                            SELECT status, COUNT(*) as count 
                            FROM shippingrecord 
                            GROUP BY status 
                            ORDER BY status
                        ) stats
                    )
                    ELSE 'No shippingrecord table found'
                END as status_summary;
        """))
        
        row = result.fetchone()
        if row and row[0]:
            print(f"  {row[0]}")
        else:
            print("  No shipping records found")
            
    except Exception as e:
        print(f"  Could not retrieve status distribution: {e}")
    
    print("ShippingStatus enum fix completed successfully!")


def downgrade():
    """
    Revert to previous state (not recommended in production)
    """
    # Convert back to text
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'shippingrecord') THEN
                ALTER TABLE shippingrecord ALTER COLUMN status TYPE text;
            END IF;
        END
        $$;
    """)
    
    # Drop the enum type
    op.execute("""
        DROP TYPE IF EXISTS shippingstatus CASCADE;
    """) 