"""Fix user role enum case mismatch

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # First, convert the column from enum to string so we can update the values
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role TYPE varchar(20)")
    
    # Now update any existing lowercase role values to uppercase (now that it's a string column)
    op.execute("UPDATE \"user\" SET role = 'ADMIN' WHERE role = 'admin'")
    op.execute("UPDATE \"user\" SET role = 'MANAGER' WHERE role = 'manager'")
    op.execute("UPDATE \"user\" SET role = 'OFFICER' WHERE role = 'officer'")
    op.execute("UPDATE \"user\" SET role = 'PRINTER' WHERE role = 'printer'")
    op.execute("UPDATE \"user\" SET role = 'VIEWER' WHERE role = 'viewer'")
    
    # Drop the existing enum type
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    
    # Create the new enum type with uppercase values
    op.execute("""
        CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'OFFICER', 'PRINTER', 'VIEWER')
    """)
    
    # Convert the column back to the enum type
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role TYPE userrole USING role::userrole")
    
    # Set the default value
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role SET DEFAULT 'OFFICER'::userrole")


def downgrade():
    # Convert column back to string
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role TYPE varchar(20)")
    
    # Drop the uppercase enum
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    
    # Recreate the lowercase enum
    op.execute("""
        CREATE TYPE userrole AS ENUM ('admin', 'manager', 'officer', 'printer', 'viewer')
    """)
    
    # Update the data back to lowercase
    op.execute("UPDATE \"user\" SET role = 'admin' WHERE role = 'ADMIN'")
    op.execute("UPDATE \"user\" SET role = 'manager' WHERE role = 'MANAGER'")
    op.execute("UPDATE \"user\" SET role = 'officer' WHERE role = 'OFFICER'")
    op.execute("UPDATE \"user\" SET role = 'printer' WHERE role = 'PRINTER'")
    op.execute("UPDATE \"user\" SET role = 'viewer' WHERE role = 'VIEWER'")
    
    # Convert back to enum type
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role TYPE userrole USING role::userrole")
    
    # Set the default value
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role SET DEFAULT 'officer'::userrole") 