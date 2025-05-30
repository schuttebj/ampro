#!/usr/bin/env python3
"""
Deployment script to fix enum data issues in production.

This script runs the necessary Alembic migration to fix the PrintJobStatus enum
and other enum data mismatches that are causing the current errors.

Usage:
    python deploy_enum_fix.py

This should be run as part of your deployment process after pulling the latest code.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main deployment function."""
    print("🚀 AMPRO License System - Enum Fix Deployment")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("alembic.ini").exists():
        print("❌ Error: alembic.ini not found. Please run this script from the AMPRO Licence directory.")
        sys.exit(1)
    
    # Check if alembic is available
    if not run_command("python -c 'import alembic'", "Checking Alembic installation"):
        print("❌ Alembic is not installed. Please install dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Show current migration status
    print("\n📋 Current database migration status:")
    run_command("alembic current", "Checking current migration")
    
    # Show pending migrations
    print("\n📋 Pending migrations:")
    run_command("alembic heads", "Checking migration heads")
    
    # Run the enum fix migration
    print("\n🔧 Running enum fix migration...")
    if not run_command("alembic upgrade 014", "Applying enum fix migration (014)"):
        print("\n⚠️  Migration 014 failed. Trying to upgrade to latest head...")
        if not run_command("alembic upgrade head", "Upgrading to latest migration"):
            print("❌ Migration failed. Please check the database connection and try again.")
            sys.exit(1)
    
    # Verify the fix
    print("\n✅ Enum fix deployment completed!")
    print("\nNext steps:")
    print("1. Restart your application server")
    print("2. Test the print queue functionality")
    print("3. Monitor the logs for enum-related errors")
    
    print("\n📝 If you still see enum errors after restart:")
    print("1. Check the database enum values: SELECT DISTINCT status FROM printjob;")
    print("2. Verify all values are uppercase: QUEUED, ASSIGNED, PRINTING, etc.")
    print("3. Contact the development team if issues persist")

if __name__ == "__main__":
    main() 