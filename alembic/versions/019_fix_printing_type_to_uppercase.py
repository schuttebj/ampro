"""Fix printing_type to use uppercase values

Revision ID: 019
Revises: 018
Create Date: 2025-05-30 12:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    """
    Convert printing_type values to uppercase to match Python enum.
    """
    
    # Check if location table exists and convert printing_type values to uppercase
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
                    WHEN UPPER(printing_type) = 'LOCAL' THEN 'LOCAL'
                    WHEN UPPER(printing_type) = 'CENTRALIZED' THEN 'CENTRALIZED'
                    WHEN UPPER(printing_type) = 'HYBRID' THEN 'HYBRID'
                    WHEN UPPER(printing_type) = 'DISABLED' THEN 'DISABLED'
                    ELSE 'LOCAL'  -- Default fallback
                END
                WHERE printing_type IS NOT NULL;
                
                -- Step 4: Drop and recreate the enum type with uppercase values
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
    Revert to lowercase values
    """
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'location') THEN
                -- Convert back to text
                ALTER TABLE location ALTER COLUMN printing_type DROP DEFAULT;
                ALTER TABLE location ALTER COLUMN printing_type TYPE text;
                
                -- Convert to lowercase
                UPDATE location 
                SET printing_type = CASE 
                    WHEN printing_type = 'LOCAL' THEN 'local'
                    WHEN printing_type = 'CENTRALIZED' THEN 'centralized'
                    WHEN printing_type = 'HYBRID' THEN 'hybrid'
                    WHEN printing_type = 'DISABLED' THEN 'disabled'
                    ELSE 'local'
                END;
                
                -- Recreate with lowercase
                DROP TYPE IF EXISTS printingtype;
                CREATE TYPE printingtype AS ENUM ('local', 'centralized', 'hybrid', 'disabled');
                
                ALTER TABLE location ALTER COLUMN printing_type TYPE printingtype USING printing_type::printingtype;
                ALTER TABLE location ALTER COLUMN printing_type SET DEFAULT 'local'::printingtype;
            END IF;
        END
        $$;
    """) 