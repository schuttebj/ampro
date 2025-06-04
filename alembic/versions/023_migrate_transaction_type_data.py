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
    
    # Map existing audit transaction types to license transaction types
    transaction_type_mapping = {
        'APPLICATION_APPROVAL': 'DRIVING_LICENCE',
        'application_approval': 'DRIVING_LICENCE',
        'APPLICATION_SUBMISSION': 'DRIVING_LICENCE', 
        'application_submission': 'DRIVING_LICENCE',
        'LICENSE_ISSUANCE': 'DRIVING_LICENCE',
        'license_issuance': 'DRIVING_LICENCE',
        'LICENSE_RENEWAL': 'DRIVING_LICENCE',
        'license_renewal': 'DRIVING_LICENCE',
        'LICENSE_REPLACEMENT': 'ID_PAPER_REPLACEMENT',
        'license_replacement': 'ID_PAPER_REPLACEMENT',
        'FEE_PAYMENT': 'DRIVING_LICENCE',
        'fee_payment': 'DRIVING_LICENCE',
        'DOCUMENT_UPLOAD': 'DRIVING_LICENCE',
        'document_upload': 'DRIVING_LICENCE'
    }
    
    # First, check what existing values we have
    connection = op.get_bind()
    
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
        print(f"Setting {null_count} NULL transaction_type records to 'DRIVING_LICENCE'")
        connection.execute(sa.text("""
            UPDATE licenseapplication 
            SET transaction_type = 'DRIVING_LICENCE' 
            WHERE transaction_type IS NULL
        """))
        connection.commit()
    
    # Check for any remaining invalid values
    final_check = connection.execute(sa.text("""
        SELECT DISTINCT transaction_type, COUNT(*) as count
        FROM licenseapplication 
        WHERE transaction_type NOT IN (
            'DRIVING_LICENCE', 'GOVT_DEPT_LICENCE', 'FOREIGN_REPLACEMENT',
            'ID_PAPER_REPLACEMENT', 'TEMPORARY_LICENCE', 'NEW_LICENCE_CARD',
            'CHANGE_PARTICULARS', 'CHANGE_LICENCE_DOC'
        )
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
                SET transaction_type = 'DRIVING_LICENCE' 
                WHERE transaction_type = :invalid_value
            """), {"invalid_value": value})
        connection.commit()
        print("Set all invalid values to 'DRIVING_LICENCE'")
    
    print("Transaction type data migration completed successfully!")


def downgrade():
    """
    Revert transaction_type values back to audit enum values if needed
    """
    
    # This is a data migration, so downgrade is optional
    # We could map license types back to audit types, but it's not critical
    print("Downgrade for transaction type data migration - no action needed")
    pass 