"""add_initial_hardware_data

Revision ID: 021
Revises: 020
Create Date: 2024-12-19 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add initial hardware data for testing webcam functionality
    """
    
    # Check if hardware table exists
    connection = op.get_bind()
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'hardware'
        );
    """)).scalar()
    
    if table_exists:
        # Insert initial webcam hardware devices
        op.execute("""
            INSERT INTO hardware (
                name, code, hardware_type, model, manufacturer, 
                serial_number, device_id, status, capabilities, 
                settings, notes, usage_count, error_count, 
                created_at, updated_at, is_active
            ) VALUES 
            (
                'Primary Webcam', 
                'WEBCAM001', 
                'WEBCAM', 
                'HD Pro Webcam', 
                'System', 
                'SYS-WC-001', 
                '0', 
                'ACTIVE', 
                '{"max_resolution": "1920x1080", "formats": ["jpeg", "png"], "fps": 30}',
                '{"quality": "high", "auto_focus": true, "auto_exposure": true}',
                'Primary webcam device (device index 0) for citizen photo capture',
                0,
                0,
                NOW(),
                NOW(),
                true
            ),
            (
                'Secondary Webcam', 
                'WEBCAM002', 
                'WEBCAM', 
                'Standard Webcam', 
                'System', 
                'SYS-WC-002', 
                '1', 
                'ACTIVE', 
                '{"max_resolution": "1280x720", "formats": ["jpeg", "png"], "fps": 30}',
                '{"quality": "medium", "auto_focus": true, "auto_exposure": true}',
                'Secondary webcam device (device index 1) for backup photo capture',
                0,
                0,
                NOW(),
                NOW(),
                true
            )
            ON CONFLICT (code) DO NOTHING;
        """)


def downgrade():
    """
    Remove initial hardware data
    """
    op.execute("""
        DELETE FROM hardware 
        WHERE code IN ('WEBCAM001', 'WEBCAM002');
    """) 