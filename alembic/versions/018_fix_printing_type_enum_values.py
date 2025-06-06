"""Fix printing_type enum values

Revision ID: 018
Revises: 017
Create Date: 2025-05-30 12:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix printing_type enum values by ensuring they are uppercase to match SQLAlchemy expectations.
    """
    
    # Check if location table exists and fix printing_type values
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'location') THEN
                -- Step 1: Remove default value constraint first
                ALTER TABLE location ALTER COLUMN printing_type DROP DEFAULT;
                
                -- Step 2: Convert column to text to allow string operations
                ALTER TABLE location ALTER COLUMN printing_type TYPE text;
                
                -- Step 3: Convert any lowercase printing_type values to uppercase
                UPDATE location 
                SET printing_type = CASE 
                    WHEN LOWER(printing_type) = 'local' THEN 'LOCAL'
                    WHEN LOWER(printing_type) = 'centralized' THEN 'CENTRALIZED'
                    WHEN LOWER(printing_type) = 'hybrid' THEN 'HYBRID'
                    WHEN LOWER(printing_type) = 'disabled' THEN 'DISABLED'
                    ELSE 'LOCAL'  -- Default fallback
                END
                WHERE printing_type IS NOT NULL;
                
                -- Step 4: Now we can safely drop and recreate the enum type with uppercase values
                DROP TYPE IF EXISTS printingtype;
                CREATE TYPE printingtype AS ENUM ('LOCAL', 'CENTRALIZED', 'HYBRID', 'DISABLED');
                
                -- Step 5: Convert back to enum
                ALTER TABLE location ALTER COLUMN printing_type TYPE printingtype USING printing_type::printingtype;
                
                -- Step 6: Restore default value with uppercase
                ALTER TABLE location ALTER COLUMN printing_type SET DEFAULT 'LOCAL'::printingtype;
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
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'location') THEN
                ALTER TABLE location ALTER COLUMN printing_type TYPE text;
            END IF;
        END
        $$;
        DROP TYPE IF EXISTS printingtype;
    """) 