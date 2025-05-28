"""Add locations and location relationships

Revision ID: add_locations_and_relationships
Revises: add_application_type
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_locations_and_relationships'
down_revision = 'add_application_type'
branch_labels = None
depends_on = None


def upgrade():
    # Create locations table
    op.create_table('location',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('address_line1', sa.String(length=255), nullable=False),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state_province', sa.String(length=100), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False, server_default='South Africa'),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('manager_name', sa.String(length=100), nullable=True),
        sa.Column('operating_hours', sa.Text(), nullable=True),
        sa.Column('services_offered', sa.Text(), nullable=True),
        sa.Column('capacity_per_day', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('accepts_applications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('accepts_collections', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for location table
    op.create_index('ix_location_name', 'location', ['name'])
    op.create_index('ix_location_code', 'location', ['code'])
    op.create_unique_constraint('uq_location_code', 'location', ['code'])
    
    # Add location_id to user table
    op.add_column('user', sa.Column('location_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_user_location', 'user', 'location', ['location_id'], ['id'])
    
    # Add location_id to licenseapplication table
    op.add_column('licenseapplication', sa.Column('location_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_licenseapplication_location', 'licenseapplication', 'location', ['location_id'], ['id'])


def downgrade():
    # Remove foreign key constraints
    op.drop_constraint('fk_licenseapplication_location', 'licenseapplication', type_='foreignkey')
    op.drop_constraint('fk_user_location', 'user', type_='foreignkey')
    
    # Remove location_id columns
    op.drop_column('licenseapplication', 'location_id')
    op.drop_column('user', 'location_id')
    
    # Drop location table indexes and constraints
    op.drop_constraint('uq_location_code', 'location', type_='unique')
    op.drop_index('ix_location_code', 'location')
    op.drop_index('ix_location_name', 'location')
    
    # Drop locations table
    op.drop_table('location') 