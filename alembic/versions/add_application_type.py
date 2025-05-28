"""Add application type and previous license fields

Revision ID: add_application_type
Revises: 006_add_iso_compliance_fields
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_application_type'
down_revision = '006_add_iso_compliance_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create the application_type enum
    application_type_enum = postgresql.ENUM(
        'new', 'renewal', 'replacement', 'upgrade', 'conversion',
        name='applicationtype'
    )
    application_type_enum.create(op.get_bind())
    
    # Add the new columns
    op.add_column('licenseapplication', 
        sa.Column('application_type', 
                  sa.Enum('new', 'renewal', 'replacement', 'upgrade', 'conversion', 
                         name='applicationtype'),
                  nullable=False,
                  server_default='new'))
    
    op.add_column('licenseapplication',
        sa.Column('previous_license_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_licenseapplication_previous_license',
        'licenseapplication', 'license',
        ['previous_license_id'], ['id']
    )


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_licenseapplication_previous_license', 'licenseapplication', type_='foreignkey')
    
    # Remove columns
    op.drop_column('licenseapplication', 'previous_license_id')
    op.drop_column('licenseapplication', 'application_type')
    
    # Drop the enum type
    application_type_enum = postgresql.ENUM(
        'new', 'renewal', 'replacement', 'upgrade', 'conversion',
        name='applicationtype'
    )
    application_type_enum.drop(op.get_bind()) 