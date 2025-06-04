#!/usr/bin/env python3
"""
Deploy Enhanced Fields Migration

This script applies the migration to add enhanced citizen and license application fields
to fix the database schema mismatch causing the 500 errors.

Usage:
    python deploy_enhanced_fields.py
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command, description):
    """Run a shell command and handle errors"""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        logger.info(f"Success: {description}")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Exit code: {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        if e.stdout:
            logger.error(f"Output: {e.stdout}")
        return False


def check_database_connection():
    """Check if we can connect to the database"""
    logger.info("Checking database connection...")
    
    # Try to connect using alembic
    return run_command(
        "python -c \"from alembic import command; from alembic.config import Config; config = Config('alembic.ini'); command.current(config)\"",
        "Test database connection"
    )


def backup_database():
    """Create a backup before running migrations (if possible)"""
    logger.info("Creating database backup...")
    
    # In production, this would use pg_dump
    # For now, just log that we're starting
    logger.info("Database backup step - would create backup in production")
    return True


def apply_migration():
    """Apply the enhanced fields migration"""
    logger.info("Applying enhanced fields migration...")
    
    # Show current migration state
    run_command(
        "alembic current",
        "Show current migration state"
    )
    
    # Show pending migrations
    run_command(
        "alembic heads",
        "Show available migration heads"
    )
    
    # Apply the migration
    success = run_command(
        "alembic upgrade head",
        "Apply enhanced fields migration"
    )
    
    if success:
        logger.info("Migration applied successfully!")
        
        # Show new migration state
        run_command(
            "alembic current",
            "Show updated migration state"
        )
    
    return success


def verify_migration():
    """Verify that the new fields exist in the database"""
    logger.info("Verifying migration results...")
    
    # Test queries to verify the new fields exist
    test_queries = [
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'citizen' AND column_name = 'identification_type';",
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'licenseapplication' AND column_name = 'transaction_type';",
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'licenseapplication' AND column_name = 'photograph_attached';",
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'licenseapplication' AND column_name = 'information_true_correct';"
    ]
    
    verification_script = f"""
import os
import psycopg2
from urllib.parse import urlparse

# Get database URL from environment
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("No DATABASE_URL found")
    exit(1)

try:
    # Parse the database URL
    parsed = urlparse(database_url)
    
    # Connect to database
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],  # Remove leading slash
        user=parsed.username,
        password=parsed.password,
        sslmode='require'
    )
    
    cursor = conn.cursor()
    
    # Test queries
    test_queries = {test_queries}
    
    print("Checking for new database fields...")
    
    all_passed = True
    for query in test_queries:
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            print(f"✓ Found field: {{result[0]}}")
        else:
            print(f"✗ Missing field from query: {{query}}")
            all_passed = False
    
    if all_passed:
        print("\\n✓ All enhanced fields verified successfully!")
    else:
        print("\\n✗ Some fields are missing")
        exit(1)
        
    conn.close()
    
except Exception as e:
    print(f"Error verifying migration: {{e}}")
    exit(1)
"""
    
    # Write and run verification script
    with open('verify_migration.py', 'w') as f:
        f.write(verification_script)
    
    success = run_command(
        "python verify_migration.py",
        "Verify new database fields exist"
    )
    
    # Clean up
    if os.path.exists('verify_migration.py'):
        os.remove('verify_migration.py')
    
    return success


def main():
    """Main deployment function"""
    logger.info("=" * 60)
    logger.info("AMPRO Enhanced Fields Migration Deployment")
    logger.info("=" * 60)
    logger.info(f"Start time: {datetime.now()}")
    
    steps = [
        ("Check database connection", check_database_connection),
        ("Create database backup", backup_database),
        ("Apply migration", apply_migration),
        ("Verify migration", verify_migration),
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n--- Step: {step_name} ---")
        
        if not step_func():
            logger.error(f"Step failed: {step_name}")
            logger.error("Deployment stopped due to failure")
            sys.exit(1)
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ Enhanced fields migration deployment completed successfully!")
    logger.info(f"End time: {datetime.now()}")
    logger.info("=" * 60)
    
    logger.info("\nNext steps:")
    logger.info("1. Verify frontend can now access the API without errors")
    logger.info("2. Test the enhanced application form functionality")
    logger.info("3. Monitor backend logs for any remaining issues")


if __name__ == "__main__":
    main() 