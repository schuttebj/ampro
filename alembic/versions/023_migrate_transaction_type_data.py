"""Migrate transaction_type data from audit enum to license enum values

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
    Migrate existing transaction_type values from old audit enum to new license enum values
    """
    
    connection = op.get_bind()
    
    # Check what enum values exist in the database
    existing_enum_values = connection.execute(sa.text("""
        SELECT enumlabel 
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'transactiontype'
        ORDER BY enumlabel
    """)).fetchall()
    
    enum_values = [row[0] for row in existing_enum_values]
    print(f"Available enum values in database: {enum_values}")
    
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
    print("Current transaction_type values in licenseapplication table:")
    for value, count in existing_values:
        print(f"  - {value}: {count} records")
    
    # Map old audit enum values to new license enum values
    value_mappings = {
        # Old audit values -> New license values
        'APPLICATION_APPROVAL': 'DRIVING_LICENCE',
        'APPLICATION_SUBMISSION': 'DRIVING_LICENCE', 
        'APPLICATION_REJECTION': 'DRIVING_LICENCE',
        'LICENSE_ISSUANCE': 'DRIVING_LICENCE',
        'LICENSE_RENEWAL': 'DRIVING_LICENCE',
        'LICENSE_REPLACEMENT': 'NEW_LICENCE_CARD',
        'FEE_PAYMENT': 'DRIVING_LICENCE',
        'DOCUMENT_UPLOAD': 'DRIVING_LICENCE',
        # Lowercase versions too (just in case)
        'application_approval': 'DRIVING_LICENCE',
        'application_submission': 'DRIVING_LICENCE',
        'application_rejection': 'DRIVING_LICENCE',
        'license_issuance': 'DRIVING_LICENCE',
        'license_renewal': 'DRIVING_LICENCE',
        'license_replacement': 'NEW_LICENCE_CARD',
        'fee_payment': 'DRIVING_LICENCE',
        'document_upload': 'DRIVING_LICENCE'
    }
    
    # Migrate each value
    migration_count = 0
    for old_value, new_value in value_mappings.items():
        # Check if this old value exists in data
        count_result = connection.execute(sa.text("""
            SELECT COUNT(*) 
            FROM licenseapplication 
            WHERE transaction_type = :old_value
        """), {"old_value": old_value})
        
        count = count_result.scalar()
        if count > 0:
            # Verify the new value exists in enum
            if new_value in enum_values:
                print(f"Migrating {count} records from '{old_value}' -> '{new_value}'")
                
                connection.execute(sa.text("""
                    UPDATE licenseapplication 
                    SET transaction_type = :new_value 
                    WHERE transaction_type = :old_value
                """), {"old_value": old_value, "new_value": new_value})
                
                migration_count += count
            else:
                print(f"ERROR: Target value '{new_value}' not found in enum for '{old_value}'")
    
    # Handle any NULL values
    null_count = connection.execute(sa.text("""
        SELECT COUNT(*) 
        FROM licenseapplication 
        WHERE transaction_type IS NULL
    """)).scalar()
    
    if null_count > 0:
        default_value = 'DRIVING_LICENCE' if 'DRIVING_LICENCE' in enum_values else enum_values[0]
        print(f"Setting {null_count} NULL transaction_type records to '{default_value}'")
        
        connection.execute(sa.text("""
            UPDATE licenseapplication 
            SET transaction_type = :default_value 
            WHERE transaction_type IS NULL
        """), {"default_value": default_value})
        migration_count += null_count
    
    # Commit all changes
    connection.commit()
    
    # Final verification
    final_result = connection.execute(sa.text("""
        SELECT DISTINCT transaction_type, COUNT(*) as count
        FROM licenseapplication 
        GROUP BY transaction_type
        ORDER BY count DESC
    """))
    
    final_values = final_result.fetchall()
    print("Final transaction_type values after migration:")
    
    all_valid = True
    for value, count in final_values:
        if value in enum_values:
            print(f"  ✓ {value}: {count} records")
        else:
            print(f"  ✗ {value}: {count} records (INVALID!)")
            all_valid = False
    
    if all_valid:
        print(f"✅ Migration completed successfully! {migration_count} records updated.")
    else:
        print("❌ Some values are still invalid after migration!")
    
    print("Transaction type data migration completed!")


def downgrade():
    """
    Revert transaction_type values back to audit enum values
    """
    connection = op.get_bind()
    
    # Reverse mappings
    reverse_mappings = {
        'DRIVING_LICENCE': 'APPLICATION_APPROVAL',
        'NEW_LICENCE_CARD': 'LICENSE_REPLACEMENT',
        'GOVT_DEPT_LICENCE': 'LICENSE_ISSUANCE',
        'FOREIGN_REPLACEMENT': 'LICENSE_REPLACEMENT',
        'ID_PAPER_REPLACEMENT': 'LICENSE_REPLACEMENT',
        'TEMPORARY_LICENCE': 'LICENSE_ISSUANCE',
        'CHANGE_PARTICULARS': 'APPLICATION_APPROVAL',
        'CHANGE_LICENCE_DOC': 'APPLICATION_APPROVAL'
    }
    
    print("Reverting transaction type values...")
    
    for new_value, old_value in reverse_mappings.items():
        count_result = connection.execute(sa.text("""
            SELECT COUNT(*) 
            FROM licenseapplication 
            WHERE transaction_type = :new_value
        """), {"new_value": new_value})
        
        count = count_result.scalar()
        if count > 0:
            print(f"Reverting {count} records from '{new_value}' -> '{old_value}'")
            connection.execute(sa.text("""
                UPDATE licenseapplication 
                SET transaction_type = :old_value 
                WHERE transaction_type = :new_value
            """), {"new_value": new_value, "old_value": old_value})
    
    connection.commit()
    print("Transaction type data reversion completed!")
    pass 