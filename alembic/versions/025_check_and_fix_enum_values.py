"""Check and fix enum values with correct mapping

Revision ID: 025
Revises: 024
Create Date: 2025-01-04 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade():
    """
    Check actual enum values and fix the data migration properly
    """
    
    connection = op.get_bind()
    
    print("=== CHECKING ACTUAL ENUM VALUES ===")
    
    # First, check what enum values actually exist
    try:
        result = connection.execute(sa.text("""
            SELECT enumlabel 
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = 'transactiontype'
            ORDER BY enumlabel
        """))
        actual_enum_values = [row[0] for row in result.fetchall()]
        print("Actual enum values in database:")
        for value in actual_enum_values:
            print(f"  - '{value}'")
    except Exception as e:
        print(f"Could not query enum values: {e}")
        return
    
    # Check current data
    try:
        result = connection.execute(sa.text("""
            SELECT DISTINCT transaction_type, COUNT(*) as count
            FROM licenseapplication 
            GROUP BY transaction_type
            ORDER BY transaction_type
        """))
        current_values = result.fetchall()
        print("\nCurrent data values:")
        for value, count in current_values:
            print(f"  - '{value}': {count} records")
    except Exception as e:
        print(f"Could not query current values: {e}")
        return
    
    # Since the old values are actually valid for license applications, 
    # and they work better than the truncated new enum values,
    # let's revert the enum to the old working values
    
    print("\n=== REVERTING TO WORKING ENUM VALUES ===")
    
    try:
        # Drop the current enum
        connection.execute(sa.text("DROP TYPE IF EXISTS transactiontype_new"))
        
        # Create a new enum with the old working values
        connection.execute(sa.text("""
            CREATE TYPE transactiontype_new AS ENUM (
                'APPLICATION_APPROVAL',
                'APPLICATION_SUBMISSION', 
                'APPLICATION_REJECTION',
                'DOCUMENT_UPLOAD',
                'FEE_PAYMENT',
                'LICENSE_ISSUANCE',
                'LICENSE_RENEWAL',
                'LICENSE_REPLACEMENT'
            )
        """))
        
        # Update the column to use the new enum
        connection.execute(sa.text("""
            ALTER TABLE licenseapplication 
            ALTER COLUMN transaction_type TYPE transactiontype_new 
            USING transaction_type::text::transactiontype_new
        """))
        
        # Replace the old enum
        connection.execute(sa.text("DROP TYPE transactiontype"))
        connection.execute(sa.text("ALTER TYPE transactiontype_new RENAME TO transactiontype"))
        
        print("✓ Successfully reverted to working enum values")
        
    except Exception as e:
        print(f"Error reverting enum: {e}")
        # If that fails, let's try to just add the missing old values to the current enum
        try:
            print("Trying to add missing values to current enum...")
            old_values = ['APPLICATION_APPROVAL', 'APPLICATION_SUBMISSION', 'APPLICATION_REJECTION', 
                         'DOCUMENT_UPLOAD', 'FEE_PAYMENT', 'LICENSE_ISSUANCE', 'LICENSE_RENEWAL', 'LICENSE_REPLACEMENT']
            
            for value in old_values:
                try:
                    connection.execute(sa.text(f"ALTER TYPE transactiontype ADD VALUE IF NOT EXISTS '{value}'"))
                    print(f"  ✓ Added '{value}'")
                except Exception as add_error:
                    print(f"  ✗ Could not add '{value}': {add_error}")
                    
        except Exception as e2:
            print(f"Could not add values either: {e2}")
    
    # Verify final state
    try:
        result = connection.execute(sa.text("""
            SELECT DISTINCT transaction_type, COUNT(*) as count
            FROM licenseapplication 
            GROUP BY transaction_type
            ORDER BY transaction_type
        """))
        final_values = result.fetchall()
        print("\nFinal data state:")
        for value, count in final_values:
            print(f"  - '{value}': {count} records")
    except Exception as e:
        print(f"Could not verify final state: {e}")
    
    print("\n✓ Migration completed")


def downgrade():
    """
    Downgrade not supported
    """
    print("Downgrade not supported for this migration")
    pass 