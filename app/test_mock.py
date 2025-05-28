"""
Test script to identify issues with the mock.py file
"""
from fastapi import FastAPI, Depends
from app.api.v1.endpoints.mock import generate_test_data
from app.api.v1.dependencies import get_db
from app.db.session import SessionLocal
from app.core.security import get_current_active_superuser
from app.models.user import User

# Test function to manually examine the generate_test_data function
def test_generate_data():
    # Get a database session
    db = SessionLocal()
    
    try:
        # Create a fake superuser for testing
        test_user = User(
            id=1,
            full_name="Test Admin",
            username="admin",
            email="admin@example.com",
            hashed_password="test",
            is_active=True,
            is_superuser=True
        )
        
        # Call the function
        result = generate_test_data(
            db=db,
            num_citizens=2,
            num_licenses=1,
            num_applications=1,
            current_user=test_user
        )
        
        print("Test result:", result)
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        # Print exception chain
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing generate_test_data function...")
    test_generate_data() 