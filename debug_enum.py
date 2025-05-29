#!/usr/bin/env python3
"""
Debug script to check enum values and database state
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.license import PrintJobStatus
from app.db.session import SessionLocal
from sqlalchemy import text

def test_enum_values():
    """Test enum values"""
    print("=== PrintJobStatus Enum Values ===")
    for status in PrintJobStatus:
        print(f"  {status.name} = '{status.value}'")
    
    print(f"\nQUEUED value: '{PrintJobStatus.QUEUED.value}'")
    print(f"ASSIGNED value: '{PrintJobStatus.ASSIGNED.value}'")

def test_database_enum():
    """Test database enum"""
    db = SessionLocal()
    try:
        print("\n=== Database Enum Check ===")
        # Check if enum type exists
        result = db.execute(text("""
            SELECT typname, enumlabel 
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE typname = 'printjobstatus'
            ORDER BY enumlabel
        """)).fetchall()
        
        if result:
            print("Database enum values:")
            for row in result:
                print(f"  '{row.enumlabel}'")
        else:
            print("No printjobstatus enum found in database!")
            
        # Try to create a simple query
        print("\n=== Testing Query ===")
        try:
            test_query = text("SELECT 1 WHERE 'queued'::printjobstatus = 'queued'::printjobstatus")
            result = db.execute(test_query).fetchone()
            print("✓ Basic enum query works")
        except Exception as e:
            print(f"✗ Basic enum query failed: {e}")
            
        # Test the problematic query
        print("\n=== Testing Print Queue Query ===")
        try:
            test_query = text("""
                SELECT COUNT(*) 
                FROM printjob 
                WHERE status IN ('queued'::printjobstatus, 'assigned'::printjobstatus)
            """)
            result = db.execute(test_query).fetchone()
            print(f"✓ Print queue query works, count: {result[0]}")
        except Exception as e:
            print(f"✗ Print queue query failed: {e}")
            
    except Exception as e:
        print(f"Database connection error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_enum_values()
    test_database_enum() 