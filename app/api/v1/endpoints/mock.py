from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import faker
from faker import Faker
import random
from datetime import date, datetime, timedelta

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_superuser, get_password_hash
from app.models.citizen import Gender, MaritalStatus
from app.models.license import LicenseCategory, LicenseStatus, ApplicationStatus
from app.models.audit import ActionType, ResourceType, TransactionType, TransactionStatus
from app.models.user import User
from app.schemas.user import UserCreate

router = APIRouter()

# Initialize faker
fake = Faker()


@router.post("/setup-admin", response_model=Dict[str, Any])
def setup_admin_user(
    *,
    db: Session = Depends(get_db),
) -> Any:
    """
    Create an admin user for testing. Anyone can call this endpoint.
    In a production environment, this would be removed.
    """
    # Check if admin already exists
    admin = crud.user.get_by_username(db, username="admin")
    if admin:
        return {
            "message": "Admin user already exists",
            "username": "admin",
            "password": "The password is not shown for security reasons"
        }
    
    # Create admin user
    password = "admin123"  # For testing only
    admin_user = crud.user.create(
        db, 
        obj_in=UserCreate(
            username="admin",
            email="admin@example.com",
            password=password,
            full_name="Admin User",
            is_superuser=True,
            department="Administration"
        )
    )
    
    return {
        "message": "Admin user created successfully",
        "username": admin_user.username,
        "password": password
    }


@router.post("/generate-data", response_model=Dict[str, Any])
def generate_test_data(
    *,
    db: Session = Depends(get_db),
    num_citizens: int = 10,
    num_licenses: int = 5,
    num_applications: int = 3,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Generate test data for the system. Only for superusers.
    """
    fake = Faker('en_ZA')  # South African locale
    
    # Generate citizens
    created_citizens = []
    for _ in range(num_citizens):
        # Generate random South African ID number (13 digits)
        # This is a simplified version and doesn't validate against the checksum
        yy = str(random.randint(60, 99)).zfill(2)
        mm = str(random.randint(1, 12)).zfill(2)
        dd = str(random.randint(1, 28)).zfill(2)
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        id_number = f"{yy}{mm}{dd}{random_digits}"
        
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        birth_year = int(f"19{yy}")
        birth_month = int(mm)
        birth_day = int(dd)
        
        # Create citizen
        try:
            citizen = crud.citizen.create(
                db,
                obj_in={
                    "id_number": id_number,
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "middle_name": fake.first_name() if random.random() > 0.7 else None,
                    "date_of_birth": date(birth_year, birth_month, birth_day),
                    "gender": gender,
                    "marital_status": random.choice(list(MaritalStatus)),
                    "phone_number": fake.phone_number(),
                    "email": fake.email(),
                    "address_line1": fake.street_address(),
                    "address_line2": fake.secondary_address() if random.random() > 0.7 else None,
                    "city": fake.city(),
                    "state_province": fake.province(),
                    "postal_code": fake.postcode(),
                    "country": "South Africa",
                    "birth_place": fake.city(),
                    "nationality": "South African",
                }
            )
            created_citizens.append(citizen)
        except Exception as e:
            # Skip if there's an error (like duplicate ID)
            continue
    
    # Generate licenses
    created_licenses = []
    for citizen in created_citizens[:num_licenses]:
        try:
            license_number = crud.license.generate_license_number()
            license = crud.license.create(
                db,
                obj_in={
                    "license_number": license_number,
                    "citizen_id": citizen.id,
                    "category": random.choice(list(LicenseCategory)),
                    "issue_date": date.today() - timedelta(days=random.randint(1, 365*3)),
                    "expiry_date": date.today() + timedelta(days=random.randint(1, 365*5)),
                    "status": random.choice(list(LicenseStatus)),
                    "restrictions": fake.text(max_nb_chars=100) if random.random() > 0.7 else None,
                    "medical_conditions": fake.text(max_nb_chars=100) if random.random() > 0.7 else None,
                }
            )
            created_licenses.append(license)
        except Exception as e:
            # Skip if there's an error
            continue
    
    # Generate applications
    created_applications = []
    for citizen in created_citizens[num_licenses:num_licenses+num_applications]:
        try:
            application = crud.license_application.create(
                db,
                obj_in={
                    "citizen_id": citizen.id,
                    "applied_category": random.choice(list(LicenseCategory)),
                    "status": random.choice(list(ApplicationStatus)),
                    "application_date": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    "documents_verified": random.choice([True, False]),
                    "medical_verified": random.choice([True, False]),
                    "payment_verified": random.choice([True, False]),
                    "review_notes": fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
                }
            )
            created_applications.append(application)
        except Exception as e:
            # Skip if there's an error
            continue
    
    # Generate transactions
    created_transactions = []
    for license in created_licenses:
        try:
            transaction = crud.transaction.create(
                db,
                obj_in={
                    "transaction_type": TransactionType.LICENSE_ISSUANCE,
                    "transaction_ref": crud.transaction.generate_transaction_ref(),
                    "status": TransactionStatus.COMPLETED,
                    "user_id": current_user.id,
                    "citizen_id": license.citizen_id,
                    "license_id": license.id,
                    "initiated_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    "completed_at": datetime.utcnow() - timedelta(days=random.randint(0, 29)),
                    "amount": random.randint(10000, 50000),  # Amount in cents (R100-R500)
                    "notes": "Test transaction",
                }
            )
            created_transactions.append(transaction)
        except Exception as e:
            # Skip if there's an error
            continue
    
    # Generate audit logs
    created_logs = []
    for citizen in created_citizens:
        try:
            log = crud.audit_log.create(
                db,
                obj_in={
                    "user_id": current_user.id,
                    "action_type": ActionType.CREATE,
                    "resource_type": ResourceType.CITIZEN,
                    "resource_id": str(citizen.id),
                    "timestamp": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                    "description": f"Created citizen record for {citizen.first_name} {citizen.last_name}",
                }
            )
            created_logs.append(log)
        except Exception as e:
            # Skip if there's an error
            continue
    
    return {
        "message": "Test data generated successfully",
        "citizens_created": len(created_citizens),
        "licenses_created": len(created_licenses),
        "applications_created": len(created_applications),
        "transactions_created": len(created_transactions),
        "audit_logs_created": len(created_logs),
    }


@router.post("/reset-database", response_model=Dict[str, Any])
def reset_database(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Reset the database by truncating all tables except users.
    Only for superusers and only for development/testing.
    """
    # This is a simplified and dangerous method - in a real system,
    # you would use migrations or a proper database reset method
    try:
        # Delete all records from tables (except users)
        db.execute("DELETE FROM auditlog")
        db.execute("DELETE FROM transaction")
        db.execute("DELETE FROM licenseapplication")
        db.execute("DELETE FROM license")
        db.execute("DELETE FROM citizen")
        
        # Reset sequences (PostgreSQL specific)
        db.execute("ALTER SEQUENCE auditlog_id_seq RESTART WITH 1")
        db.execute("ALTER SEQUENCE transaction_id_seq RESTART WITH 1")
        db.execute("ALTER SEQUENCE licenseapplication_id_seq RESTART WITH 1")
        db.execute("ALTER SEQUENCE license_id_seq RESTART WITH 1")
        db.execute("ALTER SEQUENCE citizen_id_seq RESTART WITH 1")
        
        db.commit()
        return {
            "message": "Database reset successfully",
            "warning": "All data except users has been deleted"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset database: {str(e)}",
        ) 