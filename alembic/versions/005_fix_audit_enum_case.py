"""Fix audit enum case mismatch

Revision ID: 005
Revises: 004
Create Date: 2024-01-15 12:00:00.000000

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
    # Handle ActionType enum
    # First, convert the column from enum to string so we can update the values
    op.execute("ALTER TABLE auditlog ALTER COLUMN action_type TYPE varchar(20)")
    
    # Now update any existing lowercase action_type values to uppercase
    op.execute("UPDATE auditlog SET action_type = 'CREATE' WHERE action_type = 'create'")
    op.execute("UPDATE auditlog SET action_type = 'READ' WHERE action_type = 'read'")
    op.execute("UPDATE auditlog SET action_type = 'UPDATE' WHERE action_type = 'update'")
    op.execute("UPDATE auditlog SET action_type = 'DELETE' WHERE action_type = 'delete'")
    op.execute("UPDATE auditlog SET action_type = 'LOGIN' WHERE action_type = 'login'")
    op.execute("UPDATE auditlog SET action_type = 'LOGOUT' WHERE action_type = 'logout'")
    op.execute("UPDATE auditlog SET action_type = 'PRINT' WHERE action_type = 'print'")
    op.execute("UPDATE auditlog SET action_type = 'EXPORT' WHERE action_type = 'export'")
    op.execute("UPDATE auditlog SET action_type = 'VERIFY' WHERE action_type = 'verify'")
    
    # Drop the existing enum type
    op.execute("DROP TYPE IF EXISTS actiontype CASCADE")
    
    # Create the new enum type with uppercase values
    op.execute("""
        CREATE TYPE actiontype AS ENUM ('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'PRINT', 'EXPORT', 'VERIFY')
    """)
    
    # Convert the column back to the enum type
    op.execute("ALTER TABLE auditlog ALTER COLUMN action_type TYPE actiontype USING action_type::actiontype")
    
    # Handle ResourceType enum
    # First, convert the column from enum to string so we can update the values
    op.execute("ALTER TABLE auditlog ALTER COLUMN resource_type TYPE varchar(20)")
    
    # Now update any existing lowercase resource_type values to uppercase
    op.execute("UPDATE auditlog SET resource_type = 'USER' WHERE resource_type = 'user'")
    op.execute("UPDATE auditlog SET resource_type = 'CITIZEN' WHERE resource_type = 'citizen'")
    op.execute("UPDATE auditlog SET resource_type = 'LICENSE' WHERE resource_type = 'license'")
    op.execute("UPDATE auditlog SET resource_type = 'APPLICATION' WHERE resource_type = 'application'")
    op.execute("UPDATE auditlog SET resource_type = 'FILE' WHERE resource_type = 'file'")
    op.execute("UPDATE auditlog SET resource_type = 'SYSTEM' WHERE resource_type = 'system'")
    
    # Drop the existing enum type
    op.execute("DROP TYPE IF EXISTS resourcetype CASCADE")
    
    # Create the new enum type with uppercase values
    op.execute("""
        CREATE TYPE resourcetype AS ENUM ('USER', 'CITIZEN', 'LICENSE', 'APPLICATION', 'FILE', 'SYSTEM')
    """)
    
    # Convert the column back to the enum type
    op.execute("ALTER TABLE auditlog ALTER COLUMN resource_type TYPE resourcetype USING resource_type::resourcetype")


def downgrade():
    # Handle ActionType enum - convert back to lowercase
    op.execute("ALTER TABLE auditlog ALTER COLUMN action_type TYPE varchar(20)")
    
    # Drop the uppercase enum
    op.execute("DROP TYPE IF EXISTS actiontype CASCADE")
    
    # Recreate the lowercase enum
    op.execute("""
        CREATE TYPE actiontype AS ENUM ('create', 'read', 'update', 'delete', 'login', 'logout', 'print', 'export', 'verify')
    """)
    
    # Update the data back to lowercase
    op.execute("UPDATE auditlog SET action_type = 'create' WHERE action_type = 'CREATE'")
    op.execute("UPDATE auditlog SET action_type = 'read' WHERE action_type = 'READ'")
    op.execute("UPDATE auditlog SET action_type = 'update' WHERE action_type = 'UPDATE'")
    op.execute("UPDATE auditlog SET action_type = 'delete' WHERE action_type = 'DELETE'")
    op.execute("UPDATE auditlog SET action_type = 'login' WHERE action_type = 'LOGIN'")
    op.execute("UPDATE auditlog SET action_type = 'logout' WHERE action_type = 'LOGOUT'")
    op.execute("UPDATE auditlog SET action_type = 'print' WHERE action_type = 'PRINT'")
    op.execute("UPDATE auditlog SET action_type = 'export' WHERE action_type = 'EXPORT'")
    op.execute("UPDATE auditlog SET action_type = 'verify' WHERE action_type = 'VERIFY'")
    
    # Convert back to enum type
    op.execute("ALTER TABLE auditlog ALTER COLUMN action_type TYPE actiontype USING action_type::actiontype")
    
    # Handle ResourceType enum - convert back to lowercase
    op.execute("ALTER TABLE auditlog ALTER COLUMN resource_type TYPE varchar(20)")
    
    # Drop the uppercase enum
    op.execute("DROP TYPE IF EXISTS resourcetype CASCADE")
    
    # Recreate the lowercase enum
    op.execute("""
        CREATE TYPE resourcetype AS ENUM ('user', 'citizen', 'license', 'application', 'file', 'system')
    """)
    
    # Update the data back to lowercase
    op.execute("UPDATE auditlog SET resource_type = 'user' WHERE resource_type = 'USER'")
    op.execute("UPDATE auditlog SET resource_type = 'citizen' WHERE resource_type = 'CITIZEN'")
    op.execute("UPDATE auditlog SET resource_type = 'license' WHERE resource_type = 'LICENSE'")
    op.execute("UPDATE auditlog SET resource_type = 'application' WHERE resource_type = 'APPLICATION'")
    op.execute("UPDATE auditlog SET resource_type = 'file' WHERE resource_type = 'FILE'")
    op.execute("UPDATE auditlog SET resource_type = 'system' WHERE resource_type = 'SYSTEM'")
    
    # Convert back to enum type
    op.execute("ALTER TABLE auditlog ALTER COLUMN resource_type TYPE resourcetype USING resource_type::resourcetype") 