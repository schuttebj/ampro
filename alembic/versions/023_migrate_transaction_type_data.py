"""Migrate existing transaction_type data to license-specific enum values

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
    Migrate existing transaction_type values to license-specific enum values
    """
    
    connection = op.get_bind()
    
    # First, check what enum values actually exist
    existing_enum_values = connection.execute(sa.text("""
        SELECT enumlabel 
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'transactiontype'
        ORDER BY enumlabel
    """)).fetchall()
    
    enum_values = [row[0] for row in existing_enum_values]
    print(f"Available enum values: {enum_values}")
    
    # Determine target value based on what's available
    if 'DRIVING_LICENCE' in enum_values:
        target_value = 'DRIVING_LICENCE'
        print("Using uppercase enum values")
    elif 'driving_licence' in enum_values:
        target_value = 'driving_licence'
        print("Using lowercase enum values")
    elif enum_values:
        # Use the first available value as fallback
        target_value = enum_values[0]
        print(f"Using fallback enum value: {target_value}")
    else:
        print("ERROR: No enum values found!")
        return
    
    # Map existing audit transaction types to license transaction types
    transaction_type_mapping = {
        'APPLICATION_APPROVAL': target_value,
        'application_approval': target_value,
        'APPLICATION_SUBMISSION': target_value, 
        'application_submission': target_value,
        'LICENSE_ISSUANCE': target_value,
        'license_issuance': target_value,
        'LICENSE_RENEWAL': target_value,
        'license_renewal': target_value,
        'LICENSE_REPLACEMENT': target_value,  # Map to same for simplicity
        'license_replacement': target_value,
        'FEE_PAYMENT': target_value,
        'fee_payment': target_value,
        'DOCUMENT_UPLOAD': target_value,
        'document_upload': target_value
    }
    
    # Get all distinct transaction_type values in the licenseapplication table
    result = connection.execute(sa.text("""
        SELECT DISTINCT transaction_type, COUNT(*) as count
        FROM licenseapplication 
        WHERE transaction_type IS NOT NULL
        GROUP BY transaction_type
        ORDER BY count DESC
    """))
    
    existing_values = result.fetchall()
    print("Existing transaction_type values in database:")
    for value, count in existing_values:
        print(f"  - {value}: {count} records")
    
    # Update each problematic value
    for old_value, new_value in transaction_type_mapping.items():
        # Check if this value exists
        check_result = connection.execute(sa.text("""
            SELECT COUNT(*) 
            FROM licenseapplication 
            WHERE transaction_type = :old_value
        """), {"old_value": old_value})
        
        count = check_result.scalar()
        if count > 0:
            print(f"Updating {count} records from '{old_value}' to '{new_value}'")
            
            # Update the records
            connection.execute(sa.text("""
                UPDATE licenseapplication 
                SET transaction_type = :new_value 
                WHERE transaction_type = :old_value
            """), {"old_value": old_value, "new_value": new_value})
            
            # Commit the changes
            connection.commit()
        else:
            print(f"No records found with transaction_type = '{old_value}'")
    
    # Set any remaining NULL or unknown values to default
    null_count = connection.execute(sa.text("""
        SELECT COUNT(*) 
        FROM licenseapplication 
        WHERE transaction_type IS NULL
    """)).scalar()
    
    if null_count > 0:
        print(f"Setting {null_count} NULL transaction_type records to '{target_value}'")
        connection.execute(sa.text("""
            UPDATE licenseapplication 
            SET transaction_type = :target_value 
            WHERE transaction_type IS NULL
        """), {"target_value": target_value})
        connection.commit()
    
    # Check for any remaining invalid values - build dynamic validation based on available enum values
    if enum_values:
        placeholders = ','.join([f"'{val}'" for val in enum_values])
        final_check = connection.execute(sa.text(f"""
            SELECT DISTINCT transaction_type, COUNT(*) as count
            FROM licenseapplication 
            WHERE transaction_type NOT IN ({placeholders})
            GROUP BY transaction_type
        """))
        
        invalid_values = final_check.fetchall()
        if invalid_values:
            print("Found remaining invalid transaction_type values:")
            for value, count in invalid_values:
                print(f"  - {value}: {count} records")
                # Set them to default
                connection.execute(sa.text("""
                    UPDATE licenseapplication 
                    SET transaction_type = :target_value 
                    WHERE transaction_type = :invalid_value
                """), {"target_value": target_value, "invalid_value": value})
            connection.commit()
            print(f"Set all invalid values to '{target_value}'")
    
    print("Transaction type data migration completed successfully!")


def downgrade():
    """
    Revert transaction_type values back to audit enum values if needed
    """
    
    # This is a data migration, so downgrade is optional
    # We could map license types back to audit types, but it's not critical
    print("Downgrade for transaction type data migration - no action needed")
    pass 