#!/usr/bin/env python3
"""
Test ShippingStatus Enum Fix

This script tests the ShippingStatus enum on the server to confirm the fix works.

Usage:
    python test_shipping_enum.py
"""

import requests
import sys

def test_shipping_statistics():
    """Test the shipping statistics endpoint that was failing"""
    
    print("🧪 Testing ShippingStatus Enum Fix")
    print("=" * 50)
    
    # Test the endpoint that was failing
    url = "https://ampro-licence.onrender.com/api/v1/workflow/statistics/shipping"
    
    print(f"Testing endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Shipping statistics endpoint working!")
            
            # Try to parse JSON response
            try:
                data = response.json()
                print(f"Response data: {data}")
                
                # Check if we have shipping stats
                if 'shipping' in data or 'shipping_stats' in data:
                    print("✅ Shipping statistics data returned successfully")
                else:
                    print("⚠️  Response doesn't contain expected shipping data")
                    
            except Exception as e:
                print(f"⚠️  Could not parse JSON response: {e}")
                print(f"Raw response: {response.text[:200]}...")
                
        elif response.status_code == 500:
            print("❌ FAILED: Internal server error (likely enum issue)")
            print(f"Error response: {response.text[:200]}...")
            
            # Check if it's the specific enum error
            if "invalid input value for enum shippingstatus" in response.text.lower():
                print("🔍 CONFIRMED: This is the ShippingStatus enum error we need to fix")
                return False
            else:
                print("🔍 Different server error")
                
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("❌ FAILED: Request timeout")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False
    
    return response.status_code == 200

def test_enum_values():
    """Test ShippingStatus enum values"""
    
    print("\n🔍 ShippingStatus Enum Analysis")
    print("=" * 40)
    
    try:
        # Import the enum (this would work on server)
        from app.models.license import ShippingStatus
        
        print("Python ShippingStatus enum values:")
        for status in ShippingStatus:
            print(f"  {status.name} = '{status.value}'")
            
        print("\nExpected database values (should match Python):")
        print("  pending, in_transit, delivered, failed")
        
        print("\nProblem:")
        print("  Database currently has: PENDING, IN_TRANSIT, DELIVERED, FAILED")
        print("  Python expects:         pending, in_transit, delivered, failed")
        print("  Solution: Migration 015 will convert database to lowercase")
        
    except ImportError:
        print("Cannot import ShippingStatus (running outside server environment)")
        print("Expected Python enum values: pending, in_transit, delivered, failed")

def main():
    """Run all tests"""
    
    print("🚀 AMPRO LICENCE - ShippingStatus Enum Testing")
    print("=" * 60)
    
    # Test enum values understanding
    test_enum_values()
    
    # Test the actual endpoint
    endpoint_working = test_shipping_statistics()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if endpoint_working:
        print("✅ ShippingStatus enum is working correctly!")
        print("   No migration needed.")
    else:
        print("❌ ShippingStatus enum needs to be fixed.")
        print("   Run the migration: alembic upgrade head")
        print("   Expected fix: Convert database enum values to lowercase")
    
    print("\n🔧 After running migration 015:")
    print("   - Database will have: pending, in_transit, delivered, failed")
    print("   - Python enum expects: pending, in_transit, delivered, failed")
    print("   - Should resolve the enum mismatch error")
    
    return 0 if endpoint_working else 1

if __name__ == "__main__":
    sys.exit(main()) 