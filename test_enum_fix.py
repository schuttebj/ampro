#!/usr/bin/env python3
"""
Test script to verify the enum fix is working correctly.

This script tests that:
1. Print job queries work without enum errors
2. Enum values are correctly handled
3. CRUD operations work with proper enum types

Usage:
    python test_enum_fix.py
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

try:
    from app.db.session import SessionLocal
    from app import crud
    from app.models.license import PrintJobStatus
    from sqlalchemy import text
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Make sure you're running this from the AMPRO Licence directory")
    sys.exit(1)

def test_database_connection():
    """Test database connection."""
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).fetchone()
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_enum_values():
    """Test that enum values match expected values."""
    expected_values = {'QUEUED', 'ASSIGNED', 'PRINTING', 'COMPLETED', 'FAILED', 'CANCELLED'}
    actual_values = {status.value for status in PrintJobStatus}
    
    if expected_values == actual_values:
        print("✅ PrintJobStatus enum values are correct")
        return True
    else:
        print(f"❌ PrintJobStatus enum values mismatch:")
        print(f"   Expected: {expected_values}")
        print(f"   Actual: {actual_values}")
        return False

def test_database_enum_values():
    """Test that database enum values match Python enum values."""
    try:
        db = SessionLocal()
        
        # Check if printjob table exists and has data
        result = db.execute(text("SELECT COUNT(*) FROM printjob")).fetchone()
        print_job_count = result[0] if result else 0
        
        if print_job_count == 0:
            print("ℹ️  No print jobs in database to test")
            db.close()
            return True
        
        # Get distinct status values from database
        result = db.execute(text("SELECT DISTINCT status FROM printjob ORDER BY status")).fetchall()
        db_values = {row[0] for row in result}
        
        # Expected values (should all be uppercase)
        expected_values = {'QUEUED', 'ASSIGNED', 'PRINTING', 'COMPLETED', 'FAILED', 'CANCELLED'}
        
        # Check if all database values are in expected values
        unexpected_values = db_values - expected_values
        
        if not unexpected_values:
            print(f"✅ Database enum values are correct: {sorted(db_values)}")
            db.close()
            return True
        else:
            print(f"❌ Database contains unexpected enum values: {unexpected_values}")
            print(f"   All values in DB: {sorted(db_values)}")
            print("   Run the enum fix migration to correct this")
            db.close()
            return False
            
    except Exception as e:
        print(f"❌ Failed to check database enum values: {e}")
        return False

def test_print_job_queries():
    """Test that print job queries work without enum errors."""
    try:
        db = SessionLocal()
        
        # Test basic query
        print_jobs = crud.print_job.get_queue(db, skip=0, limit=5)
        print(f"✅ Print queue query successful (found {len(print_jobs)} jobs)")
        
        # Test statistics query
        stats = crud.print_job.get_statistics(db)
        print(f"✅ Print job statistics query successful: {stats}")
        
        # Test status-specific query
        queued_jobs = crud.print_job.get_by_status(db, status=PrintJobStatus.QUEUED, limit=5)
        print(f"✅ Status-specific query successful (found {len(queued_jobs)} queued jobs)")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Print job queries failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 AMPRO License System - Enum Fix Test")
    print("=" * 40)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Python Enum Values", test_enum_values),
        ("Database Enum Values", test_database_enum_values),
        ("Print Job Queries", test_print_job_queries),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed: {test_name}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enum fix is working correctly.")
        print("\nYou can now:")
        print("- Test the print queue in your application")
        print("- Create new print jobs")
        print("- Use the workflow endpoints")
        return True
    else:
        print("⚠️  Some tests failed. Please:")
        print("1. Run the enum fix migration: python deploy_enum_fix.py")
        print("2. Restart your application")
        print("3. Run this test again")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 