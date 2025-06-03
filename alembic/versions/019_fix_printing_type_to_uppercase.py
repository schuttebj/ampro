"""fix_printing_type_to_uppercase

Revision ID: 019
Revises: 018
Create Date: 2024-12-19 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix printer type and status enum values to be uppercase
    """
    
    # Fix printer type enum values to uppercase
    op.execute("""
        DO $$
        BEGIN
            -- Fix printer table printer_type values if the table exists
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'printer') THEN
                -- Convert printer_type column to text first
                ALTER TABLE printer ALTER COLUMN printer_type TYPE text;
                
                -- Update values to uppercase
                UPDATE printer 
                SET printer_type = CASE 
                    WHEN LOWER(printer_type) = 'card_printer' THEN 'CARD_PRINTER'
                    WHEN LOWER(printer_type) = 'document_printer' THEN 'DOCUMENT_PRINTER'
                    WHEN LOWER(printer_type) = 'photo_printer' THEN 'PHOTO_PRINTER'
                    WHEN LOWER(printer_type) = 'thermal_printer' THEN 'THERMAL_PRINTER'
                    WHEN LOWER(printer_type) = 'inkjet_printer' THEN 'INKJET_PRINTER'
                    WHEN LOWER(printer_type) = 'laser_printer' THEN 'LASER_PRINTER'
                    ELSE 'DOCUMENT_PRINTER'  -- Default fallback
                END
                WHERE printer_type IS NOT NULL;
                
                -- Update status column to text first
                ALTER TABLE printer ALTER COLUMN status TYPE text;
                
                -- Update status values to uppercase
                UPDATE printer 
                SET status = CASE 
                    WHEN LOWER(status) = 'active' THEN 'ACTIVE'
                    WHEN LOWER(status) = 'inactive' THEN 'INACTIVE'
                    WHEN LOWER(status) = 'maintenance' THEN 'MAINTENANCE'
                    WHEN LOWER(status) = 'offline' THEN 'OFFLINE'
                    WHEN LOWER(status) = 'error' THEN 'ERROR'
                    ELSE 'ACTIVE'  -- Default fallback
                END
                WHERE status IS NOT NULL;
                
                -- Recreate enums with uppercase values
                DROP TYPE IF EXISTS printertype;
                CREATE TYPE printertype AS ENUM ('CARD_PRINTER', 'DOCUMENT_PRINTER', 'PHOTO_PRINTER', 'THERMAL_PRINTER', 'INKJET_PRINTER', 'LASER_PRINTER');
                
                DROP TYPE IF EXISTS printerstatus;
                CREATE TYPE printerstatus AS ENUM ('ACTIVE', 'INACTIVE', 'MAINTENANCE', 'OFFLINE', 'ERROR');
                
                -- Convert columns back to enum types
                ALTER TABLE printer ALTER COLUMN printer_type TYPE printertype USING printer_type::printertype;
                ALTER TABLE printer ALTER COLUMN status TYPE printerstatus USING status::printerstatus;
                
                -- Set default values
                ALTER TABLE printer ALTER COLUMN status SET DEFAULT 'ACTIVE'::printerstatus;
            END IF;
        END
        $$;
    """)


def downgrade():
    """
    Revert printer type and status enum values to lowercase
    """
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'printer') THEN
                -- Convert to text
                ALTER TABLE printer ALTER COLUMN printer_type TYPE text;
                ALTER TABLE printer ALTER COLUMN status TYPE text;
                
                -- Update to lowercase
                UPDATE printer 
                SET printer_type = CASE 
                    WHEN printer_type = 'CARD_PRINTER' THEN 'card_printer'
                    WHEN printer_type = 'DOCUMENT_PRINTER' THEN 'document_printer'
                    WHEN printer_type = 'PHOTO_PRINTER' THEN 'photo_printer'
                    WHEN printer_type = 'THERMAL_PRINTER' THEN 'thermal_printer'
                    WHEN printer_type = 'INKJET_PRINTER' THEN 'inkjet_printer'
                    WHEN printer_type = 'LASER_PRINTER' THEN 'laser_printer'
                    ELSE 'document_printer'
                END;
                
                UPDATE printer 
                SET status = CASE 
                    WHEN status = 'ACTIVE' THEN 'active'
                    WHEN status = 'INACTIVE' THEN 'inactive'
                    WHEN status = 'MAINTENANCE' THEN 'maintenance'
                    WHEN status = 'OFFLINE' THEN 'offline'
                    WHEN status = 'ERROR' THEN 'error'
                    ELSE 'active'
                END;
                
                -- Recreate enums with lowercase values
                DROP TYPE IF EXISTS printertype;
                CREATE TYPE printertype AS ENUM ('card_printer', 'document_printer', 'photo_printer', 'thermal_printer', 'inkjet_printer', 'laser_printer');
                
                DROP TYPE IF EXISTS printerstatus;
                CREATE TYPE printerstatus AS ENUM ('active', 'inactive', 'maintenance', 'offline', 'error');
                
                -- Convert back to enum
                ALTER TABLE printer ALTER COLUMN printer_type TYPE printertype USING printer_type::printertype;
                ALTER TABLE printer ALTER COLUMN status TYPE printerstatus USING status::printerstatus;
                
                ALTER TABLE printer ALTER COLUMN status SET DEFAULT 'active'::printerstatus;
            END IF;
        END
        $$;
    """) 