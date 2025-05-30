#!/usr/bin/env python3
"""
Deploy ShippingStatus Enum Fix

This script:
1. Commits and pushes the ShippingStatus enum fix to git
2. Provides instructions for running on the server

Usage:
    python deploy_shipping_fix.py
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
        print(f"❌ Error running command: {e}")
        return False
    
    return True

def main():
    """Deploy the ShippingStatus enum fix"""
    
    print("=" * 60)
    print("🚀 AMPRO LICENCE - ShippingStatus Enum Fix Deployment")
    print("=" * 60)
    
    # Change to correct directory
    ampro_dir = "AMPRO Licence"
    if os.path.exists(ampro_dir):
        os.chdir(ampro_dir)
        print(f"✅ Changed to directory: {os.getcwd()}")
    
    # Git operations
    commands = [
        ("git add .", "Adding ShippingStatus fix files"),
        ("git commit -m \"Fix: ShippingStatus enum data mismatch (uppercase to lowercase)\"", "Committing changes"),
        ("git push origin main", "Pushing to GitHub")
    ]
    
    success = True
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            success = False
            break
    
    if success:
        print("\n✅ All Git operations completed successfully!")
        
        print("\n" + "="*60)
        print("📋 SERVER DEPLOYMENT INSTRUCTIONS")
        print("="*60)
        print("""
1. SSH to your Render server or use Render's console
2. Navigate to the AMPRO Licence directory
3. Run the migration:
   
   alembic upgrade head
   
   Expected output:
   - "Fixing ShippingStatus enum..."
   - Status distribution after fix
   - "ShippingStatus enum fix completed successfully!"

4. Test the shipping statistics endpoint:
   
   curl "https://ampro-licence.onrender.com/api/v1/workflow/statistics/shipping"
   
   Should now return without enum errors.

5. Restart the FastAPI server if needed:
   
   # Render will auto-restart on git push, but manual restart if needed
        """)
        
        print("\n🔍 TROUBLESHOOTING:")
        print("- If you see 'PENDING' enum errors, the migration worked!")
        print("- Database should now accept lowercase: 'pending', 'in_transit', etc.")
        print("- Python enum values are lowercase, database is now lowercase")
        print("- Check logs for successful status distribution output")
        
    else:
        print("\n❌ Deployment failed. Please fix errors and try again.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 