"""Add LOCATION to ResourceType enum

Revision ID: 007
Revises: 006_add_iso_compliance_fields
Create Date: 2024-05-28 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006_add_iso_compliance_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add LOCATION value to the existing ResourceType enum
    op.execute("ALTER TYPE resourcetype ADD VALUE IF NOT EXISTS 'LOCATION'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum, which is complex and risky
    # For now, we'll leave the LOCATION value in the enum
    # If removal is absolutely necessary, it would require:
    # 1. Converting all columns using the enum to text
    # 2. Dropping the enum
    # 3. Recreating the enum without LOCATION
    # 4. Converting columns back to the enum
    # 5. Ensuring no data uses LOCATION value
    
    pass  # No downgrade action - enum values are typically permanent 