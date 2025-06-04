"""Add enhanced citizen and transaction fields

Revision ID: 022
Revises: 021
Create Date: 2025-01-04 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = :table_name AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.scalar() > 0


def add_column_if_not_exists(table_name, column):
    """Add a column only if it doesn't already exist"""
    if not column_exists(table_name, column.name):
        op.add_column(table_name, column)
        print(f"Added column {column.name} to {table_name}")
    else:
        print(f"Column {column.name} already exists in {table_name}, skipping")


def upgrade():
    """
    Add missing enhanced fields to citizen and licenseapplication tables
    """
    
    # Create new enum types for enhanced fields
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'identificationtype') THEN
                CREATE TYPE identificationtype AS ENUM ('RSA_ID', 'TRAFFIC_REGISTER', 'FOREIGN_ID');
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'officiallanguage') THEN
                CREATE TYPE officiallanguage AS ENUM (
                    'AFRIKAANS', 'NDEBELE', 'NORTHERN_SOTHO', 'SOTHO', 'SWAZI', 
                    'TSONGA', 'TSWANA', 'VENDA', 'XHOSA', 'ZULU'
                );
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'addresstype') THEN
                CREATE TYPE addresstype AS ENUM ('POSTAL', 'STREET');
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transactiontype') THEN
                CREATE TYPE transactiontype AS ENUM (
                    'DRIVING_LICENCE', 'GOVT_DEPT_LICENCE', 'FOREIGN_REPLACEMENT',
                    'ID_PAPER_REPLACEMENT', 'TEMPORARY_LICENCE', 'NEW_LICENCE_CARD',
                    'CHANGE_PARTICULARS', 'CHANGE_LICENCE_DOC'
                );
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cardnoticestatus') THEN
                CREATE TYPE cardnoticestatus AS ENUM ('THEFT', 'LOSS', 'DESTRUCTION', 'RECOVERY', 'NEW_CARD');
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'maritalstatus') THEN
                CREATE TYPE maritalstatus AS ENUM ('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED');
            END IF;
        END
        $$;
    """)
    
    # Add enhanced fields to citizen table - with existence checks
    add_column_if_not_exists('citizen', sa.Column('identification_type', postgresql.ENUM('RSA_ID', 'TRAFFIC_REGISTER', 'FOREIGN_ID', name='identificationtype'), nullable=False, server_default='RSA_ID'))
    add_column_if_not_exists('citizen', sa.Column('country_of_issue', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('nationality', sa.String(), nullable=True, server_default='South African'))
    add_column_if_not_exists('citizen', sa.Column('middle_name', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('initials', sa.String(10), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('marital_status', postgresql.ENUM('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED', name='maritalstatus'), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('official_language', postgresql.ENUM('AFRIKAANS', 'NDEBELE', 'NORTHERN_SOTHO', 'SOTHO', 'SWAZI', 'TSONGA', 'TSWANA', 'VENDA', 'XHOSA', 'ZULU', name='officiallanguage'), nullable=True))
    
    # Enhanced contact fields
    add_column_if_not_exists('citizen', sa.Column('phone_home', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('phone_daytime', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('phone_cell', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('fax_number', sa.String(), nullable=True))
    
    # Enhanced address fields - Postal
    add_column_if_not_exists('citizen', sa.Column('postal_suburb', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('postal_city', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('postal_code', sa.String(), nullable=True))
    
    # Enhanced address fields - Street
    add_column_if_not_exists('citizen', sa.Column('street_address', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('street_suburb', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('street_city', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('street_postal_code', sa.String(), nullable=True))
    
    # Address preference
    add_column_if_not_exists('citizen', sa.Column('preferred_address_type', postgresql.ENUM('POSTAL', 'STREET', name='addresstype'), nullable=True, server_default='POSTAL'))
    
    # Additional fields
    add_column_if_not_exists('citizen', sa.Column('birth_place', sa.String(), nullable=True))
    
    # Enhanced photo management
    add_column_if_not_exists('citizen', sa.Column('stored_photo_path', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('processed_photo_path', sa.String(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('photo_uploaded_at', sa.DateTime(), nullable=True))
    add_column_if_not_exists('citizen', sa.Column('photo_processed_at', sa.DateTime(), nullable=True))
    
    # Add transaction_type to licenseapplication table - with existence check
    if not column_exists('licenseapplication', 'transaction_type'):
        # Check if transactiontype enum exists and what values it has
        connection = op.get_bind()
        enum_check = connection.execute(sa.text("""
            SELECT string_agg(enumlabel, ',') as values
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = 'transactiontype'
        """)).scalar()
        
        if enum_check:
            print(f"Existing transactiontype enum has values: {enum_check}")
            # Use the first existing value as default, or a safe fallback
            if 'driving_licence' in enum_check.lower():
                default_value = 'DRIVING_LICENCE'
            elif 'DRIVING_LICENCE' in enum_check:
                default_value = 'DRIVING_LICENCE'
            else:
                # Use the first available value
                default_value = enum_check.split(',')[0]
            print(f"Using default value: {default_value}")
        else:
            # No existing enum, use our preferred default
            default_value = 'DRIVING_LICENCE'
            print(f"No existing enum found, using default: {default_value}")
        
        # Add the column without specifying enum values since the type already exists
        op.add_column('licenseapplication', sa.Column('transaction_type', sa.Enum(name='transactiontype'), nullable=True))
        print("Added column transaction_type to licenseapplication")
        
        # Set the default value for existing records
        op.execute(f"UPDATE licenseapplication SET transaction_type = '{default_value}' WHERE transaction_type IS NULL")
        
        # Make the column not null and set server default
        op.alter_column('licenseapplication', 'transaction_type', nullable=False, server_default=default_value)
        print(f"Set default value '{default_value}' and nullable=False for transaction_type")
    else:
        print("Column transaction_type already exists in licenseapplication, skipping")
    
    # Add enhanced Section A-D fields to licenseapplication - with existence checks
    add_column_if_not_exists('licenseapplication', sa.Column('photograph_attached', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('photograph_count', sa.Integer(), nullable=False, server_default='0'))
    
    # Section B fields
    add_column_if_not_exists('licenseapplication', sa.Column('previous_license_refusal', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('refusal_details', sa.Text(), nullable=True))
    
    # Section C fields
    add_column_if_not_exists('licenseapplication', sa.Column('card_notice_status', postgresql.ENUM('THEFT', 'LOSS', 'DESTRUCTION', 'RECOVERY', 'NEW_CARD', name='cardnoticestatus'), nullable=True))
    add_column_if_not_exists('licenseapplication', sa.Column('police_report_station', sa.String(), nullable=True))
    add_column_if_not_exists('licenseapplication', sa.Column('police_report_cas_number', sa.String(), nullable=True))
    add_column_if_not_exists('licenseapplication', sa.Column('office_of_issue', sa.String(), nullable=True))
    add_column_if_not_exists('licenseapplication', sa.Column('card_status_change_date', sa.Date(), nullable=True))
    
    # Section D: Legal declarations
    add_column_if_not_exists('licenseapplication', sa.Column('not_disqualified', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('not_suspended', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('not_cancelled', sa.Boolean(), nullable=False, server_default='false'))
    
    # Medical declarations
    add_column_if_not_exists('licenseapplication', sa.Column('no_uncontrolled_epilepsy', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('no_sudden_fainting', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('no_mental_illness', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('no_muscular_incoordination', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('no_uncontrolled_diabetes', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('no_defective_vision', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('no_unsafe_disability', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('no_narcotic_addiction', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('no_alcohol_addiction', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('medically_fit', sa.Boolean(), nullable=False, server_default='false'))
    
    # Declaration completion
    add_column_if_not_exists('licenseapplication', sa.Column('information_true_correct', sa.Boolean(), nullable=False, server_default='false'))
    add_column_if_not_exists('licenseapplication', sa.Column('applicant_signature_date', sa.Date(), nullable=True))
    
    # Draft management fields
    add_column_if_not_exists('licenseapplication', sa.Column('is_draft', sa.Boolean(), nullable=False, server_default='true'))
    add_column_if_not_exists('licenseapplication', sa.Column('submitted_at', sa.DateTime(), nullable=True))


def downgrade():
    """
    Remove enhanced fields from citizen and licenseapplication tables
    """
    
    # Remove licenseapplication enhanced fields - with existence checks
    if column_exists('licenseapplication', 'submitted_at'):
        op.drop_column('licenseapplication', 'submitted_at')
    if column_exists('licenseapplication', 'is_draft'):
        op.drop_column('licenseapplication', 'is_draft')
    if column_exists('licenseapplication', 'applicant_signature_date'):
        op.drop_column('licenseapplication', 'applicant_signature_date')
    if column_exists('licenseapplication', 'information_true_correct'):
        op.drop_column('licenseapplication', 'information_true_correct')
    if column_exists('licenseapplication', 'medically_fit'):
        op.drop_column('licenseapplication', 'medically_fit')
    if column_exists('licenseapplication', 'no_alcohol_addiction'):
        op.drop_column('licenseapplication', 'no_alcohol_addiction')
    if column_exists('licenseapplication', 'no_narcotic_addiction'):
        op.drop_column('licenseapplication', 'no_narcotic_addiction')
    if column_exists('licenseapplication', 'no_unsafe_disability'):
        op.drop_column('licenseapplication', 'no_unsafe_disability')
    if column_exists('licenseapplication', 'no_defective_vision'):
        op.drop_column('licenseapplication', 'no_defective_vision')
    if column_exists('licenseapplication', 'no_uncontrolled_diabetes'):
        op.drop_column('licenseapplication', 'no_uncontrolled_diabetes')
    if column_exists('licenseapplication', 'no_muscular_incoordination'):
        op.drop_column('licenseapplication', 'no_muscular_incoordination')
    if column_exists('licenseapplication', 'no_mental_illness'):
        op.drop_column('licenseapplication', 'no_mental_illness')
    if column_exists('licenseapplication', 'no_sudden_fainting'):
        op.drop_column('licenseapplication', 'no_sudden_fainting')
    if column_exists('licenseapplication', 'no_uncontrolled_epilepsy'):
        op.drop_column('licenseapplication', 'no_uncontrolled_epilepsy')
    if column_exists('licenseapplication', 'not_cancelled'):
        op.drop_column('licenseapplication', 'not_cancelled')
    if column_exists('licenseapplication', 'not_suspended'):
        op.drop_column('licenseapplication', 'not_suspended')
    if column_exists('licenseapplication', 'not_disqualified'):
        op.drop_column('licenseapplication', 'not_disqualified')
    if column_exists('licenseapplication', 'card_status_change_date'):
        op.drop_column('licenseapplication', 'card_status_change_date')
    if column_exists('licenseapplication', 'office_of_issue'):
        op.drop_column('licenseapplication', 'office_of_issue')
    if column_exists('licenseapplication', 'police_report_cas_number'):
        op.drop_column('licenseapplication', 'police_report_cas_number')
    if column_exists('licenseapplication', 'police_report_station'):
        op.drop_column('licenseapplication', 'police_report_station')
    if column_exists('licenseapplication', 'card_notice_status'):
        op.drop_column('licenseapplication', 'card_notice_status')
    if column_exists('licenseapplication', 'refusal_details'):
        op.drop_column('licenseapplication', 'refusal_details')
    if column_exists('licenseapplication', 'previous_license_refusal'):
        op.drop_column('licenseapplication', 'previous_license_refusal')
    if column_exists('licenseapplication', 'photograph_count'):
        op.drop_column('licenseapplication', 'photograph_count')
    if column_exists('licenseapplication', 'photograph_attached'):
        op.drop_column('licenseapplication', 'photograph_attached')
    if column_exists('licenseapplication', 'transaction_type'):
        op.drop_column('licenseapplication', 'transaction_type')
    
    # Remove citizen enhanced fields - with existence checks
    if column_exists('citizen', 'photo_processed_at'):
        op.drop_column('citizen', 'photo_processed_at')
    if column_exists('citizen', 'photo_uploaded_at'):
        op.drop_column('citizen', 'photo_uploaded_at')
    if column_exists('citizen', 'processed_photo_path'):
        op.drop_column('citizen', 'processed_photo_path')
    if column_exists('citizen', 'stored_photo_path'):
        op.drop_column('citizen', 'stored_photo_path')
    if column_exists('citizen', 'birth_place'):
        op.drop_column('citizen', 'birth_place')
    if column_exists('citizen', 'preferred_address_type'):
        op.drop_column('citizen', 'preferred_address_type')
    if column_exists('citizen', 'street_postal_code'):
        op.drop_column('citizen', 'street_postal_code')
    if column_exists('citizen', 'street_city'):
        op.drop_column('citizen', 'street_city')
    if column_exists('citizen', 'street_suburb'):
        op.drop_column('citizen', 'street_suburb')
    if column_exists('citizen', 'street_address'):
        op.drop_column('citizen', 'street_address')
    if column_exists('citizen', 'postal_code'):
        op.drop_column('citizen', 'postal_code')
    if column_exists('citizen', 'postal_city'):
        op.drop_column('citizen', 'postal_city')
    if column_exists('citizen', 'postal_suburb'):
        op.drop_column('citizen', 'postal_suburb')
    if column_exists('citizen', 'fax_number'):
        op.drop_column('citizen', 'fax_number')
    if column_exists('citizen', 'phone_cell'):
        op.drop_column('citizen', 'phone_cell')
    if column_exists('citizen', 'phone_daytime'):
        op.drop_column('citizen', 'phone_daytime')
    if column_exists('citizen', 'phone_home'):
        op.drop_column('citizen', 'phone_home')
    if column_exists('citizen', 'official_language'):
        op.drop_column('citizen', 'official_language')
    if column_exists('citizen', 'marital_status'):
        op.drop_column('citizen', 'marital_status')
    if column_exists('citizen', 'initials'):
        op.drop_column('citizen', 'initials')
    if column_exists('citizen', 'middle_name'):
        op.drop_column('citizen', 'middle_name')
    if column_exists('citizen', 'nationality'):
        op.drop_column('citizen', 'nationality')
    if column_exists('citizen', 'country_of_issue'):
        op.drop_column('citizen', 'country_of_issue')
    if column_exists('citizen', 'identification_type'):
        op.drop_column('citizen', 'identification_type')
    
    # Drop enum types if they exist
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cardnoticestatus') THEN
                DROP TYPE cardnoticestatus;
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transactiontype') THEN
                DROP TYPE transactiontype;
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'addresstype') THEN
                DROP TYPE addresstype;
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'officiallanguage') THEN
                DROP TYPE officiallanguage;
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'identificationtype') THEN
                DROP TYPE identificationtype;
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'maritalstatus') THEN
                DROP TYPE maritalstatus;
            END IF;
        END
        $$;
    """) 