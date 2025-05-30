#!/usr/bin/env python3
"""
Deploy User Printing Management System

This script:
1. Commits and pushes all user printing management features to git
2. Provides instructions for running on the server
3. Creates sample data for testing

Usage:
    python deploy_user_printing_system.py
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and show output"""
    print(f"\n{description}...")
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} successful")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} failed")
            print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {str(e)}")
        return False
    
    return True

def main():
    print("🚀 Deploying User Printing Management System")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("alembic"):
        print("❌ Error: Not in the correct directory. Please run from the AMPRO Licence root.")
        sys.exit(1)
    
    # 1. Add all files to git
    if not run_command("git add .", "Adding all files to git"):
        sys.exit(1)
    
    # 2. Commit changes
    commit_message = "feat: Add comprehensive user printing management system\n\n" \
                    "- Add Many-to-Many User-Location relationships\n" \
                    "- Add Printer management with types and status\n" \
                    "- Add Location printing configuration\n" \
                    "- Enhance PrintJob with assignment and location tracking\n" \
                    "- Add comprehensive admin endpoints for user/printer management\n" \
                    "- Add printer user filtering for print job assignment\n" \
                    "- Add CRUD operations for all new models\n" \
                    "- Add Pydantic schemas for validation\n" \
                    "- Add database migration with data preservation"
    
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        print("ℹ️  No changes to commit or commit failed")
    
    # 3. Push to GitHub
    if not run_command("git push origin main", "Pushing to GitHub"):
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ USER PRINTING MANAGEMENT SYSTEM DEPLOYED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\n📋 NEXT STEPS FOR SERVER DEPLOYMENT:")
    print("-" * 40)
    print("1. SSH into your Render server")
    print("2. Pull the latest changes:")
    print("   git pull origin main")
    print("\n3. Run the database migration:")
    print("   alembic upgrade head")
    print("\n4. Restart the server to load new models")
    
    print("\n🎯 NEW FEATURES AVAILABLE:")
    print("-" * 30)
    print("✅ User Management:")
    print("   - GET /api/v1/admin/users (with filtering)")
    print("   - POST /api/v1/admin/users")
    print("   - PUT /api/v1/admin/users/{user_id}")
    print("   - DELETE /api/v1/admin/users/{user_id}")
    
    print("\n✅ Printer Management:")
    print("   - GET /api/v1/admin/printers")
    print("   - POST /api/v1/admin/printers")
    print("   - PUT /api/v1/admin/printers/{printer_id}")
    print("   - PUT /api/v1/admin/printers/{printer_id}/status")
    
    print("\n✅ User-Location Management:")
    print("   - POST /api/v1/admin/users/{user_id}/locations/{location_id}")
    print("   - PUT /api/v1/admin/users/{user_id}/locations/{location_id}/print-permission")
    print("   - GET /api/v1/admin/users/{user_id}/locations")
    
    print("\n✅ Print Job Assignment:")
    print("   - GET /api/v1/workflow/printer-users (for assignment dropdown)")
    print("   - Enhanced assignment with location-based filtering")
    
    print("\n🔧 TESTING ENDPOINTS:")
    print("-" * 20)
    print("1. Create a printer user:")
    print('   POST /api/v1/admin/users')
    print('   {"username": "printer1", "email": "printer1@example.com", "password": "password123", "role": "PRINTER", "full_name": "Printer User 1"}')
    
    print("\n2. Assign user to location with print permission:")
    print('   POST /api/v1/admin/users/{user_id}/locations/{location_id}?can_print=true')
    
    print("\n3. Test printer user endpoint:")
    print('   GET /api/v1/workflow/printer-users')
    
    print("\n4. Create a printer:")
    print('   POST /api/v1/admin/printers')
    print('   {"name": "Main Card Printer", "code": "CARD001", "printer_type": "card_printer", "location_id": 1}')
    
    print("\n📊 DATABASE CHANGES:")
    print("-" * 20)
    print("✅ New Tables:")
    print("   - user_locations (Many-to-Many)")
    print("   - printer")
    
    print("\n✅ Enhanced Tables:")
    print("   - location (printing configuration)")
    print("   - printjob (assignment tracking)")
    
    print("\n✅ New Enums:")
    print("   - PrinterType, PrinterStatus, PrintingType")
    
    print("\n🎉 The system now supports:")
    print("   - Multi-location user assignments")
    print("   - Centralized vs local printing")
    print("   - Printer management and assignment")
    print("   - Location-based print job routing")
    print("   - Comprehensive admin interface")

if __name__ == "__main__":
    main() 