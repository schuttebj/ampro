"""Verify transaction_type data consistency

Revision ID: 023
Revises: 022
Create Date: 2025-01-04 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade():
    """
    Verify existing transaction_type values are valid and set defaults for any NULL values
    """
    
    connection = op.get_bind()
    
    # Check what enum values exist
    existing_enum_values = connection.execute(sa.text("""
        SELECT enumlabel 
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'transactiontype'
        ORDER BY enumlabel
    """)).fetchall()
    
    enum_values = [row[0] for row in existing_enum_values]
    print(f"Available enum values: {enum_values}")
    
    if not enum_values:
        print("ERROR: No enum values found!")
        return
    
    # Get current data
    result = connection.execute(sa.text("""
        SELECT DISTINCT transaction_type, COUNT(*) as count
        FROM licenseapplication 
        WHERE transaction_type IS NOT NULL
        GROUP BY transaction_type
        ORDER BY count DESC
    """))
    
    existing_values = result.fetchall()
    print("Current transaction_type values in database:")
    for value, count in existing_values:
        print(f"  - {value}: {count} records")
    
    # Verify all existing values are valid
    all_valid = True
    for value, count in existing_values:
        if value not in enum_values:
            print(f"ERROR: Invalid value '{value}' found with {count} records")
            all_valid = False
        else:
            print(f"✓ {value} is valid ({count} records)")
    
    # Handle NULL values if any
    null_count = connection.execute(sa.text("""
        SELECT COUNT(*) 
        FROM licenseapplication 
        WHERE transaction_type IS NULL
    """)).scalar()
    
    if null_count > 0:
        # Use APPLICATION_APPROVAL as default if available, otherwise first available value
        default_value = 'APPLICATION_APPROVAL' if 'APPLICATION_APPROVAL' in enum_values else enum_values[0]
        print(f"Setting {null_count} NULL transaction_type records to '{default_value}'")
        
        connection.execute(sa.text("""
            UPDATE licenseapplication 
            SET transaction_type = :default_value 
            WHERE transaction_type IS NULL
        """), {"default_value": default_value})
        connection.commit()
    
    if all_valid:
        print("✓ All transaction_type values are valid! No data migration needed.")
    else:
        print("✗ Some invalid values found - manual intervention required.")
    
    print("Transaction type verification completed!")


def downgrade():
    """
    No action needed for downgrade
    """
    print("Downgrade for transaction type verification - no action needed")
    pass 