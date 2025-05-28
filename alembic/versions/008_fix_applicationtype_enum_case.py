"""Fix ApplicationType enum case mismatch

Revision ID: 008
Revises: 007
Create Date: 2024-05-28 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Fix ApplicationType enum case mismatch
    # First, convert the column from enum to string so we can update the values
    op.execute("ALTER TABLE licenseapplication ALTER COLUMN application_type TYPE varchar(20)")
    
    # Now update any existing lowercase application_type values to uppercase
    op.execute("UPDATE licenseapplication SET application_type = 'NEW' WHERE application_type = 'new'")
    op.execute("UPDATE licenseapplication SET application_type = 'RENEWAL' WHERE application_type = 'renewal'")
    op.execute("UPDATE licenseapplication SET application_type = 'REPLACEMENT' WHERE application_type = 'replacement'")
    op.execute("UPDATE licenseapplication SET application_type = 'UPGRADE' WHERE application_type = 'upgrade'")
    op.execute("UPDATE licenseapplication SET application_type = 'CONVERSION' WHERE application_type = 'conversion'")
    
    # Drop the existing enum type
    op.execute("DROP TYPE IF EXISTS applicationtype CASCADE")
    
    # Create the new enum type with uppercase values
    op.execute("""
        CREATE TYPE applicationtype AS ENUM ('NEW', 'RENEWAL', 'REPLACEMENT', 'UPGRADE', 'CONVERSION')
    """)
    
    # Convert the column back to the enum type
    op.execute("ALTER TABLE licenseapplication ALTER COLUMN application_type TYPE applicationtype USING application_type::applicationtype")
    
    # Set the default value
    op.execute("ALTER TABLE licenseapplication ALTER COLUMN application_type SET DEFAULT 'NEW'::applicationtype")


def downgrade():
    # Convert column back to string
    op.execute("ALTER TABLE licenseapplication ALTER COLUMN application_type TYPE varchar(20)")
    
    # Drop the uppercase enum
    op.execute("DROP TYPE IF EXISTS applicationtype CASCADE")
    
    # Recreate the lowercase enum
    op.execute("""
        CREATE TYPE applicationtype AS ENUM ('new', 'renewal', 'replacement', 'upgrade', 'conversion')
    """)
    
    # Update the data back to lowercase
    op.execute("UPDATE licenseapplication SET application_type = 'new' WHERE application_type = 'NEW'")
    op.execute("UPDATE licenseapplication SET application_type = 'renewal' WHERE application_type = 'RENEWAL'")
    op.execute("UPDATE licenseapplication SET application_type = 'replacement' WHERE application_type = 'REPLACEMENT'")
    op.execute("UPDATE licenseapplication SET application_type = 'upgrade' WHERE application_type = 'UPGRADE'")
    op.execute("UPDATE licenseapplication SET application_type = 'conversion' WHERE application_type = 'CONVERSION'")
    
    # Convert back to enum type
    op.execute("ALTER TABLE licenseapplication ALTER COLUMN application_type TYPE applicationtype USING application_type::applicationtype")
    
    # Set the default value
    op.execute("ALTER TABLE licenseapplication ALTER COLUMN application_type SET DEFAULT 'new'::applicationtype") 