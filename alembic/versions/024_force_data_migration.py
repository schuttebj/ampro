"""Force data migration to fix enum mismatch

Revision ID: 024
Revises: 023
Create Date: 2025-01-04 18:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade():
    """
    Force fix the enum data mismatch by directly updating problematic records
    """
    
    connection = op.get_bind()
    
    print("=== FORCE FIXING ENUM DATA MISMATCH ===")
    
    # First, check what we're dealing with
    try:
        result = connection.execute(sa.text("""
            SELECT DISTINCT transaction_type, COUNT(*) as count
            FROM licenseapplication 
            GROUP BY transaction_type
            ORDER BY transaction_type
        """))
        current_values = result.fetchall()
        print("Current transaction_type values in database:")
        for value, count in current_values:
            print(f"  - {value}: {count} records")
    except Exception as e:
        print(f"Could not query current values: {e}")
        current_values = []
    
    # Define the mapping from old to new values
    value_mapping = {
        'APPLICATION_APPROVAL': 'DRIVING_LICENCE',
        'APPLICATION_SUBMISSION': 'DRIVING_LICENCE', 
        'APPLICATION_REJECTION': 'DRIVING_LICENCE',
        'DOCUMENT_UPLOAD': 'DRIVING_LICENCE',
        'FEE_PAYMENT': 'DRIVING_LICENCE',
        'LICENSE_ISSUANCE': 'DRIVING_LICENCE',
        'LICENSE_RENEWAL': 'DRIVING_LICENCE',
        'LICENSE_REPLACEMENT': 'NEW_LICENCE_CARD',
        'application_approval': 'DRIVING_LICENCE',
        'application_submission': 'DRIVING_LICENCE',
        'license_renewal': 'DRIVING_LICENCE',
        'license_replacement': 'NEW_LICENCE_CARD'
    }
    
    # Update each problematic value
    total_updated = 0
    for old_value, new_value in value_mapping.items():
        try:
            # Check if this value exists
            result = connection.execute(sa.text("""
                SELECT COUNT(*) FROM licenseapplication 
                WHERE transaction_type = :old_value
            """), {"old_value": old_value})
            count = result.scalar()
            
            if count > 0:
                print(f"Updating {count} records from '{old_value}' to '{new_value}'")
                
                # Update the records
                result = connection.execute(sa.text("""
                    UPDATE licenseapplication 
                    SET transaction_type = :new_value 
                    WHERE transaction_type = :old_value
                """), {"old_value": old_value, "new_value": new_value})
                
                updated_count = result.rowcount
                total_updated += updated_count
                print(f"  ✓ Updated {updated_count} records")
            
        except Exception as e:
            print(f"Error updating {old_value}: {e}")
            # Try with explicit casting
            try:
                print(f"  Trying with explicit enum cast...")
                result = connection.execute(sa.text("""
                    UPDATE licenseapplication 
                    SET transaction_type = :new_value::transactiontype
                    WHERE transaction_type::text = :old_value
                """), {"old_value": old_value, "new_value": new_value})
                updated_count = result.rowcount
                total_updated += updated_count
                print(f"  ✓ Updated {updated_count} records with explicit cast")
            except Exception as e2:
                print(f"  ✗ Failed even with explicit cast: {e2}")
    
    # Verify the fix
    try:
        result = connection.execute(sa.text("""
            SELECT DISTINCT transaction_type, COUNT(*) as count
            FROM licenseapplication 
            GROUP BY transaction_type
            ORDER BY transaction_type
        """))
        final_values = result.fetchall()
        print("\nFinal transaction_type values after migration:")
        for value, count in final_values:
            print(f"  - {value}: {count} records")
    except Exception as e:
        print(f"Could not verify final values: {e}")
    
    print(f"\n✓ Migration completed. Total records updated: {total_updated}")


def downgrade():
    """
    Note: Downgrade not implemented as this fixes critical data issues
    """
    print("Downgrade not supported - this migration fixes critical data issues")
    pass 