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


def upgrade():
    """
    Add missing enhanced fields to citizen and licenseapplication tables
    """
    
    # Create new enum types for enhanced fields
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'identificationtype') THEN
                CREATE TYPE identificationtype AS ENUM ('rsa_id', 'traffic_register', 'foreign_id');
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'officiallanguage') THEN
                CREATE TYPE officiallanguage AS ENUM (
                    'afrikaans', 'ndebele', 'northern_sotho', 'sotho', 'swazi', 
                    'tsonga', 'tswana', 'venda', 'xhosa', 'zulu'
                );
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'addresstype') THEN
                CREATE TYPE addresstype AS ENUM ('postal', 'street');
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transactiontype') THEN
                CREATE TYPE transactiontype AS ENUM (
                    'driving_licence', 'govt_dept_licence', 'foreign_replacement',
                    'id_paper_replacement', 'temporary_licence', 'new_licence_card',
                    'change_particulars', 'change_licence_doc'
                );
            END IF;
        END
        $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cardnoticestatus') THEN
                CREATE TYPE cardnoticestatus AS ENUM ('theft', 'loss', 'destruction', 'recovery', 'new_card');
            END IF;
        END
        $$;
    """)
    
    # Add enhanced fields to citizen table
    op.add_column('citizen', sa.Column('identification_type', postgresql.ENUM('rsa_id', 'traffic_register', 'foreign_id', name='identificationtype'), nullable=False, server_default='rsa_id'))
    op.add_column('citizen', sa.Column('country_of_issue', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('nationality', sa.String(), nullable=True, server_default='South African'))
    op.add_column('citizen', sa.Column('middle_name', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('initials', sa.String(10), nullable=True))
    op.add_column('citizen', sa.Column('marital_status', postgresql.ENUM('single', 'married', 'divorced', 'widowed', name='maritalstatus'), nullable=True))
    op.add_column('citizen', sa.Column('official_language', postgresql.ENUM('afrikaans', 'ndebele', 'northern_sotho', 'sotho', 'swazi', 'tsonga', 'tswana', 'venda', 'xhosa', 'zulu', name='officiallanguage'), nullable=True))
    
    # Enhanced contact fields
    op.add_column('citizen', sa.Column('phone_home', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('phone_daytime', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('phone_cell', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('fax_number', sa.String(), nullable=True))
    
    # Enhanced address fields - Postal
    op.add_column('citizen', sa.Column('postal_suburb', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('postal_city', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('postal_code', sa.String(), nullable=True))
    
    # Enhanced address fields - Street
    op.add_column('citizen', sa.Column('street_address', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('street_suburb', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('street_city', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('street_postal_code', sa.String(), nullable=True))
    
    # Address preference
    op.add_column('citizen', sa.Column('preferred_address_type', postgresql.ENUM('postal', 'street', name='addresstype'), nullable=True, server_default='postal'))
    
    # Additional fields
    op.add_column('citizen', sa.Column('birth_place', sa.String(), nullable=True))
    
    # Enhanced photo management
    op.add_column('citizen', sa.Column('stored_photo_path', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('processed_photo_path', sa.String(), nullable=True))
    op.add_column('citizen', sa.Column('photo_uploaded_at', sa.DateTime(), nullable=True))
    op.add_column('citizen', sa.Column('photo_processed_at', sa.DateTime(), nullable=True))
    
    # Add transaction_type to licenseapplication table
    op.add_column('licenseapplication', sa.Column('transaction_type', postgresql.ENUM('driving_licence', 'govt_dept_licence', 'foreign_replacement', 'id_paper_replacement', 'temporary_licence', 'new_licence_card', 'change_particulars', 'change_licence_doc', name='transactiontype'), nullable=False, server_default='driving_licence'))
    
    # Add enhanced Section A-D fields to licenseapplication
    op.add_column('licenseapplication', sa.Column('photograph_attached', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('photograph_count', sa.Integer(), nullable=False, server_default='0'))
    
    # Section B fields
    op.add_column('licenseapplication', sa.Column('previous_license_refusal', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('refusal_details', sa.Text(), nullable=True))
    
    # Section C fields
    op.add_column('licenseapplication', sa.Column('card_notice_status', postgresql.ENUM('theft', 'loss', 'destruction', 'recovery', 'new_card', name='cardnoticestatus'), nullable=True))
    op.add_column('licenseapplication', sa.Column('police_report_station', sa.String(), nullable=True))
    op.add_column('licenseapplication', sa.Column('police_report_cas_number', sa.String(), nullable=True))
    op.add_column('licenseapplication', sa.Column('office_of_issue', sa.String(), nullable=True))
    op.add_column('licenseapplication', sa.Column('card_status_change_date', sa.Date(), nullable=True))
    
    # Section D: Legal declarations
    op.add_column('licenseapplication', sa.Column('not_disqualified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('not_suspended', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('not_cancelled', sa.Boolean(), nullable=False, server_default='false'))
    
    # Medical declarations
    op.add_column('licenseapplication', sa.Column('no_uncontrolled_epilepsy', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('no_sudden_fainting', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('no_mental_illness', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('no_muscular_incoordination', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('no_uncontrolled_diabetes', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('no_defective_vision', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('no_unsafe_disability', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('no_narcotic_addiction', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('no_alcohol_addiction', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('medically_fit', sa.Boolean(), nullable=False, server_default='false'))
    
    # Declaration completion
    op.add_column('licenseapplication', sa.Column('information_true_correct', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('licenseapplication', sa.Column('applicant_signature_date', sa.Date(), nullable=True))
    
    # Draft management fields
    op.add_column('licenseapplication', sa.Column('is_draft', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('licenseapplication', sa.Column('submitted_at', sa.DateTime(), nullable=True))


def downgrade():
    """
    Remove enhanced fields from citizen and licenseapplication tables
    """
    
    # Remove licenseapplication enhanced fields
    op.drop_column('licenseapplication', 'submitted_at')
    op.drop_column('licenseapplication', 'is_draft')
    op.drop_column('licenseapplication', 'applicant_signature_date')
    op.drop_column('licenseapplication', 'information_true_correct')
    op.drop_column('licenseapplication', 'medically_fit')
    op.drop_column('licenseapplication', 'no_alcohol_addiction')
    op.drop_column('licenseapplication', 'no_narcotic_addiction')
    op.drop_column('licenseapplication', 'no_unsafe_disability')
    op.drop_column('licenseapplication', 'no_defective_vision')
    op.drop_column('licenseapplication', 'no_uncontrolled_diabetes')
    op.drop_column('licenseapplication', 'no_muscular_incoordination')
    op.drop_column('licenseapplication', 'no_mental_illness')
    op.drop_column('licenseapplication', 'no_sudden_fainting')
    op.drop_column('licenseapplication', 'no_uncontrolled_epilepsy')
    op.drop_column('licenseapplication', 'not_cancelled')
    op.drop_column('licenseapplication', 'not_suspended')
    op.drop_column('licenseapplication', 'not_disqualified')
    op.drop_column('licenseapplication', 'card_status_change_date')
    op.drop_column('licenseapplication', 'office_of_issue')
    op.drop_column('licenseapplication', 'police_report_cas_number')
    op.drop_column('licenseapplication', 'police_report_station')
    op.drop_column('licenseapplication', 'card_notice_status')
    op.drop_column('licenseapplication', 'refusal_details')
    op.drop_column('licenseapplication', 'previous_license_refusal')
    op.drop_column('licenseapplication', 'photograph_count')
    op.drop_column('licenseapplication', 'photograph_attached')
    op.drop_column('licenseapplication', 'transaction_type')
    
    # Remove citizen enhanced fields
    op.drop_column('citizen', 'photo_processed_at')
    op.drop_column('citizen', 'photo_uploaded_at')
    op.drop_column('citizen', 'processed_photo_path')
    op.drop_column('citizen', 'stored_photo_path')
    op.drop_column('citizen', 'birth_place')
    op.drop_column('citizen', 'preferred_address_type')
    op.drop_column('citizen', 'street_postal_code')
    op.drop_column('citizen', 'street_city')
    op.drop_column('citizen', 'street_suburb')
    op.drop_column('citizen', 'street_address')
    op.drop_column('citizen', 'postal_code')
    op.drop_column('citizen', 'postal_city')
    op.drop_column('citizen', 'postal_suburb')
    op.drop_column('citizen', 'fax_number')
    op.drop_column('citizen', 'phone_cell')
    op.drop_column('citizen', 'phone_daytime')
    op.drop_column('citizen', 'phone_home')
    op.drop_column('citizen', 'official_language')
    op.drop_column('citizen', 'marital_status')
    op.drop_column('citizen', 'initials')
    op.drop_column('citizen', 'middle_name')
    op.drop_column('citizen', 'nationality')
    op.drop_column('citizen', 'country_of_issue')
    op.drop_column('citizen', 'identification_type')
    
    # Drop enum types
    postgresql.ENUM(name='cardnoticestatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='transactiontype').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='addresstype').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='officiallanguage').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='identificationtype').drop(op.get_bind(), checkfirst=True) 