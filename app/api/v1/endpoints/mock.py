from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import faker
from faker import Faker
import random
from datetime import date, datetime, timedelta
from fastapi import BackgroundTasks
import logging
import asyncio

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_superuser, get_password_hash
from app.models.citizen import Gender, MaritalStatus
from app.models.license import LicenseCategory, LicenseStatus, ApplicationStatus
from app.models.audit import ActionType, ResourceType, TransactionType, TransactionStatus
from app.models.user import User
from app.schemas.user import UserCreate
from app.db.session import SessionLocal

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
    logger = logging.getLogger(__name__)
    
    fake = Faker('en_US')  # Use English (US) locale instead of en_ZA
    
    errors = []
    
    # Generate citizens
    created_citizens = []
    for i in range(num_citizens):
        try:
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
                citizen_data = {
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
                    "state_province": fake.state(),  # Use state instead of province for US locale
                    "postal_code": fake.postcode(),
                    "country": "South Africa",
                    "birth_place": fake.city(),
                    "nationality": "South African",
                }
                
                citizen = crud.citizen.create(db, obj_in=citizen_data)
                created_citizens.append(citizen)
                # Log success
                logger.info(f"Created citizen: {citizen.id_number} - {citizen.first_name} {citizen.last_name}")
            except Exception as e:
                # Log error and continue
                err_msg = f"Error creating citizen {i}: {str(e)}"
                logger.error(err_msg)
                errors.append(err_msg)
                continue
        except Exception as e:
            err_msg = f"Error generating citizen data {i}: {str(e)}"
            logger.error(err_msg)
            errors.append(err_msg)
            continue
    
    # Generate licenses
    created_licenses = []
    for i, citizen in enumerate(created_citizens[:num_licenses]):
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
            logger.info(f"Created license: {license.license_number}")
        except Exception as e:
            err_msg = f"Error creating license {i}: {str(e)}"
            logger.error(err_msg)
            errors.append(err_msg)
            continue
    
    # Generate applications
    created_applications = []
    for i, citizen in enumerate(created_citizens[num_licenses:num_licenses+num_applications]):
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
            logger.info(f"Created application: {application.id}")
        except Exception as e:
            err_msg = f"Error creating application {i}: {str(e)}"
            logger.error(err_msg)
            errors.append(err_msg)
            continue
    
    # Generate transactions
    created_transactions = []
    for i, license in enumerate(created_licenses):
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
            logger.info(f"Created transaction: {transaction.transaction_ref}")
        except Exception as e:
            err_msg = f"Error creating transaction {i}: {str(e)}"
            logger.error(err_msg)
            errors.append(err_msg)
            continue
    
    # Generate audit logs
    created_logs = []
    for i, citizen in enumerate(created_citizens):
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
            logger.info(f"Created audit log: {log.id}")
        except Exception as e:
            err_msg = f"Error creating audit log {i}: {str(e)}"
            logger.error(err_msg)
            errors.append(err_msg)
            continue
    
    result = {
        "message": "Test data generated successfully",
        "citizens_created": len(created_citizens),
        "licenses_created": len(created_licenses),
        "applications_created": len(created_applications),
        "transactions_created": len(created_transactions),
        "audit_logs_created": len(created_logs),
    }
    
    if errors:
        result["errors"] = errors[:10]  # Include first 10 errors in response
        result["error_count"] = len(errors)
    
    return result


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


@router.post("/bulk-generate-citizens", response_model=Dict[str, Any])
async def bulk_generate_citizens(
    *,
    db: Session = Depends(get_db),
    count: int = 1000,
    batch_size: int = 100,  # Allow customizing batch size
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Generate a large number of citizen records in the background.
    This endpoint will start the generation process and return immediately.
    The generation will continue in the background.
    
    - count: Number of citizens to generate (default: 1000, max: 250000)
    - batch_size: Number of records to process in each batch (default: 100, min: 10, max: 1000)
    """
    from datetime import date, timedelta
    import random
    from faker import Faker
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Limit the parameters for safety
    count = min(max(count, 1), 250000)
    batch_size = min(max(batch_size, 10), 1000)
    
    # Function to generate a valid South African ID number
    def generate_sa_id_number(birthdate: date, gender: str) -> str:
        # Format birth date components
        yy = birthdate.strftime("%y")
        mm = birthdate.strftime("%m")
        dd = birthdate.strftime("%d")
        
        # Gender and sequence
        g = random.randint(0, 4) if gender.lower() == "female" else random.randint(5, 9)
        s = random.randint(100, 999)
        
        # Citizenship and fixed value
        c = 0  # South African citizen
        a = 8  # Fixed value
        
        # Create the first 12 digits
        id_partial = f"{yy}{mm}{dd}{g}{s}{c}{a}"
        
        # Calculate checksum (Luhn algorithm)
        total = 0
        for i, digit in enumerate(id_partial):
            value = int(digit)
            if i % 2 == 0:  # Even positions (0-based indexing)
                total += value
            else:  # Odd positions
                doubled = value * 2
                total += doubled if doubled < 10 else doubled - 9
        
        check_digit = (10 - (total % 10)) % 10
        
        return f"{id_partial}{check_digit}"
    
    async def generate_citizens_background(count: int, batch_size: int = 100):
        """Background task to generate citizens in batches"""
        fake = Faker('en_US')  # Use only en_US locale
        
        # Initialize storage for stats
        start_time = time.time()
        created_count = 0
        error_count = 0
        last_log_time = start_time
        
        # Log start of process
        logger.info(f"Starting bulk generation of {count} citizens with batch size {batch_size}")
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.SYSTEM,
                "resource_type": ResourceType.SYSTEM,
                "description": f"Started bulk generation of {count} citizens with batch size {batch_size}"
            }
        )
        
        # Process in batches
        for batch_start in range(0, count, batch_size):
            batch_time_start = time.time()
            
            # Calculate batch size (may be smaller for the last batch)
            current_batch_size = min(batch_size, count - batch_start)
            batch_count = 0
            batch_errors = 0
            
            # Create a new session for each batch for isolation
            batch_db = SessionLocal()
            
            try:
                # Pre-generate the citizen data for this batch to minimize database open time
                citizens_to_create = []
                for _ in range(current_batch_size):
                    try:
                        # Generate basic demographics
                        gender = random.choice(["male", "female"])
                        gender_enum = Gender.MALE if gender == "male" else Gender.FEMALE
                        
                        # Generate birth date (18-90 years old)
                        age = random.randint(18, 90)
                        birthdate = date.today() - timedelta(days=age*365 + random.randint(0, 364))
                        
                        # Generate ID number based on birthdate and gender
                        id_number = generate_sa_id_number(birthdate, gender)
                        
                        # Generate name based on gender
                        first_name = fake.first_name_male() if gender == "male" else fake.first_name_female()
                        
                        # Create citizen dictionary
                        citizen = {
                            "id_number": id_number,
                            "first_name": first_name,
                            "last_name": fake.last_name(),
                            "middle_name": fake.first_name() if random.random() > 0.7 else None,
                            "date_of_birth": birthdate,
                            "gender": gender_enum,
                            "marital_status": random.choice(list(MaritalStatus)),
                            "phone_number": fake.phone_number(),
                            "email": fake.email(),
                            "address_line1": fake.street_address(),
                            "address_line2": fake.secondary_address() if random.random() > 0.7 else None,
                            "city": fake.city(),
                            "state_province": fake.state(),
                            "postal_code": fake.postcode(),
                            "country": "South Africa",
                            "birth_place": fake.city(),
                            "nationality": "South African",
                        }
                        citizens_to_create.append(citizen)
                    except Exception as e:
                        logger.error(f"Error pre-generating citizen data: {str(e)}")
                        batch_errors += 1
                
                # Now insert all the pre-generated citizens, skipping any that already exist
                for citizen_data in citizens_to_create:
                    try:
                        # Check if ID already exists - faster than catching an exception
                        existing = crud.citizen.get_by_id_number(batch_db, id_number=citizen_data["id_number"])
                        if existing:
                            continue
                        
                        # Create the citizen record
                        crud.citizen.create(batch_db, obj_in=citizen_data)
                        batch_count += 1
                    except Exception as e:
                        logger.error(f"Error creating citizen with ID {citizen_data.get('id_number')}: {str(e)}")
                        batch_errors += 1
                
                # Commit the batch as a single transaction
                batch_db.commit()
                
                # Update counters
                created_count += batch_count
                error_count += batch_errors
                
                # Log progress periodically (every 5000 records or 30 seconds)
                current_time = time.time()
                if created_count % 5000 == 0 or (current_time - last_log_time) > 30:
                    elapsed = current_time - start_time
                    rate = created_count / elapsed if elapsed > 0 else 0
                    batch_time = current_time - batch_time_start
                    
                    progress_message = (
                        f"Bulk generation progress: {created_count}/{count} citizens created "
                        f"({rate:.1f} records/second, last batch: {batch_count} records in {batch_time:.2f}s)"
                    )
                    
                    logger.info(progress_message)
                    crud.audit_log.create(
                        batch_db,
                        obj_in={
                            "user_id": current_user.id,
                            "action_type": ActionType.SYSTEM,
                            "resource_type": ResourceType.SYSTEM,
                            "description": progress_message
                        }
                    )
                    last_log_time = current_time
                
                # Small sleep to prevent overloading the database
                await asyncio.sleep(0.1)
            
            except Exception as e:
                # Handle batch-level errors
                batch_db.rollback()
                logger.error(f"Error in bulk generation batch: {str(e)}")
                error_count += current_batch_size  # Assume all records in the batch failed
                
                # Log the error
                try:
                    crud.audit_log.create(
                        db,  # Use the main DB session
                        obj_in={
                            "user_id": current_user.id,
                            "action_type": ActionType.ERROR,
                            "resource_type": ResourceType.SYSTEM,
                            "description": f"Error in bulk generation batch: {str(e)}"
                        }
                    )
                except Exception:
                    # If we can't even log the error, just continue
                    pass
                
                # Wait a bit longer before retrying after errors
                await asyncio.sleep(1)
            finally:
                # Always close the batch session
                batch_db.close()
        
        # Final audit log with summary
        total_time = time.time() - start_time
        rate = created_count / total_time if total_time > 0 else 0
        
        completion_message = (
            f"Completed bulk generation: {created_count} citizens created, {error_count} errors, "
            f"in {total_time:.1f} seconds ({rate:.1f} records/second)"
        )
        
        logger.info(completion_message)
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.SYSTEM,
                "resource_type": ResourceType.SYSTEM,
                "description": completion_message
            }
        )
    
    # Start the background task
    background_tasks.add_task(generate_citizens_background, count, batch_size)
    
    return {
        "message": f"Started bulk generation of {count} citizens in the background with batch size {batch_size}",
        "status": "processing",
        "check_progress": "Use the /api/v1/audit endpoint to check progress logs"
    }


@router.get("/citizen-count", response_model=Dict[str, Any])
def get_citizen_count(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get the total number of citizens in the database.
    Only accessible to superusers.
    """
    try:
        # Import models
        from app.models.citizen import Citizen
        
        # Count citizens
        citizen_count = db.query(Citizen).count()
        
        return {
            "status": "ok",
            "count": citizen_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        } 