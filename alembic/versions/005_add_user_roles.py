"""Add user roles

Revision ID: 005
Revises: 004
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for user roles
    user_role_enum = postgresql.ENUM(
        'admin', 'manager', 'officer', 'printer', 'viewer',
        name='userrole',
        create_type=False
    )
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    # Add role column to user table
    op.add_column('user', sa.Column('role', user_role_enum, nullable=False, server_default='officer'))
    
    # Update existing superusers to admin role
    op.execute("UPDATE \"user\" SET role = 'admin' WHERE is_superuser = true")


def downgrade():
    # Remove role column
    op.drop_column('user', 'role')
    
    # Drop enum type
    user_role_enum = postgresql.ENUM(
        'admin', 'manager', 'officer', 'printer', 'viewer',
        name='userrole'
    )
    user_role_enum.drop(op.get_bind(), checkfirst=True) 