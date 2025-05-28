#!/usr/bin/env python3
"""
Script to create a printer user account for the AMPRO license system.
This user will have the PRINTER role and can only access print job processing functions.
"""

import sys
import os
from sqlalchemy.orm import Session
from getpass import getpass

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import get_db
from app.crud.crud_user import user as user_crud
from app.models.user import UserRole
from app.schemas.user import UserCreate


def create_printer_user():
    """Create a printer user account"""
    print("AMPRO License System - Printer User Creation")
    print("=" * 50)
    
    # Get user input
    username = input("Enter username for printer operator: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        return False
    
    email = input("Enter email for printer operator: ").strip()
    if not email:
        print("Error: Email cannot be empty")
        return False
    
    full_name = input("Enter full name for printer operator (optional): ").strip()
    
    password = getpass("Enter password for printer operator: ")
    if not password:
        print("Error: Password cannot be empty")
        return False
    
    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        print("Error: Passwords do not match")
        return False
    
    department = input("Enter department (optional): ").strip() or None
    
    # Create database session
    db = next(get_db())
    
    try:
        # Check if user already exists
        existing_user = user_crud.get_by_username(db, username=username)
        if existing_user:
            print(f"Error: User with username '{username}' already exists")
            return False
        
        existing_email = user_crud.get_by_email(db, email=email)
        if existing_email:
            print(f"Error: User with email '{email}' already exists")
            return False
        
        # Create user data
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=full_name or None,
            is_active=True,
            is_superuser=False,
            role=UserRole.PRINTER,
            department=department
        )
        
        # Create user
        new_user = user_crud.create(db, obj_in=user_data)
        
        print("\n" + "=" * 50)
        print("✅ Printer user created successfully!")
        print(f"   User ID: {new_user.id}")
        print(f"   Username: {new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Full Name: {new_user.full_name or 'Not provided'}")
        print(f"   Role: {new_user.role.value}")
        print(f"   Department: {new_user.department or 'Not specified'}")
        print("\nThis user can now:")
        print("- Login to the system with PRINTER role")
        print("- Access the printer dashboard at /printer")
        print("- View and process assigned print jobs")
        print("- Start and complete print jobs")
        print("- View application details for printing")
        print("- Access printer statistics")
        print("\nThis user CANNOT:")
        print("- Access admin functions")
        print("- Create or modify applications")
        print("- Manage other users")
        print("- Access workflow management")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Main function"""
    if create_printer_user():
        print("\nPrinter user creation completed successfully!")
        sys.exit(0)
    else:
        print("\nPrinter user creation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 