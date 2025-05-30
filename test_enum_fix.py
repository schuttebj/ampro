#!/usr/bin/env python3
"""
Test script to verify PrintJobStatus enum fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.license import PrintJobStatus

def test_enum_values():
    """Test enum values are uppercase"""
    print("=== PrintJobStatus Enum Values (After Fix) ===")
    for status in PrintJobStatus:
        print(f"  {status.name} = '{status.value}'")
    
    # Test specific values
    assert PrintJobStatus.QUEUED.value == "QUEUED", f"Expected 'QUEUED', got '{PrintJobStatus.QUEUED.value}'"
    assert PrintJobStatus.ASSIGNED.value == "ASSIGNED", f"Expected 'ASSIGNED', got '{PrintJobStatus.ASSIGNED.value}'"
    assert PrintJobStatus.PRINTING.value == "PRINTING", f"Expected 'PRINTING', got '{PrintJobStatus.PRINTING.value}'"
    assert PrintJobStatus.COMPLETED.value == "COMPLETED", f"Expected 'COMPLETED', got '{PrintJobStatus.COMPLETED.value}'"
    assert PrintJobStatus.FAILED.value == "FAILED", f"Expected 'FAILED', got '{PrintJobStatus.FAILED.value}'"
    assert PrintJobStatus.CANCELLED.value == "CANCELLED", f"Expected 'CANCELLED', got '{PrintJobStatus.CANCELLED.value}'"
    
    print("\n✓ All enum values are correct (uppercase)")
    return True

if __name__ == "__main__":
    try:
        test_enum_values()
        print("\n✅ Enum fix verification PASSED")
    except Exception as e:
        print(f"\n❌ Enum fix verification FAILED: {e}")
        sys.exit(1) 