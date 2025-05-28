"""Add GENERATE to ActionType enum

Revision ID: 009
Revises: 008
Create Date: 2024-05-28 22:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Add GENERATE value to the existing ActionType enum
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'GENERATE'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum, which is complex and risky
    # For now, we'll leave the GENERATE value in the enum
    # If removal is absolutely necessary, it would require:
    # 1. Converting all columns using the enum to text
    # 2. Dropping the enum
    # 3. Recreating the enum without GENERATE
    # 4. Converting columns back to the enum
    # 5. Ensuring no data uses GENERATE value
    
    pass  # No downgrade action - enum values are typically permanent 