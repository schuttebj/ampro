from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType
from app.models.license import ApplicationStatus
from app.models.user import User
from app.schemas.license import (
    LicenseApplication, 
    LicenseApplicationCreate, 
    LicenseApplicationUpdate
)

router = APIRouter()


@router.get("/", response_model=List[LicenseApplication])
def read_applications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve license applications.
    """
    applications = crud.license_application.get_multi(db, skip=skip, limit=limit)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.APPLICATION,
            "description": f"User {current_user.username} retrieved list of license applications"
        }
    )
    
    return applications


@router.post("/", response_model=LicenseApplication)
def create_application(
    *,
    db: Session = Depends(get_db),
    application_in: LicenseApplicationCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new license application.
    """
    # Check if citizen exists
    citizen = crud.citizen.get(db, id=application_in.citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Create application
    application = crud.license_application.create(db, obj_in=application_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(application.id),
            "description": f"User {current_user.username} created license application for citizen {citizen.id_number}"
        }
    )
    
    # Create transaction record
    crud.transaction.create(
        db,
        obj_in={
            "transaction_type": "application_submission",
            "transaction_ref": crud.transaction.generate_transaction_ref(),
            "status": "pending",
            "user_id": current_user.id,
            "citizen_id": citizen.id,
            "application_id": application.id,
            "notes": f"License application submitted for {citizen.first_name} {citizen.last_name}"
        }
    )
    
    return application


@router.get("/pending", response_model=List[Dict])
def read_pending_applications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get pending license applications.
    """
    applications = crud.license_application.get_by_status(
        db, status=ApplicationStatus.SUBMITTED, skip=skip, limit=limit
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.APPLICATION,
            "description": f"User {current_user.username} viewed pending license applications"
        }
    )
    
    # Convert to dict to avoid pydantic validation issues
    return jsonable_encoder(applications)


@router.get("/{application_id}", response_model=Dict)
def read_application(
    *,
    db: Session = Depends(get_db),
    application_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get license application by ID.
    """
    application = crud.license_application.get(db, id=application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License application not found",
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(application.id),
            "description": f"User {current_user.username} viewed license application {application.id}"
        }
    )
    
    # Convert to dict to avoid pydantic validation issues
    return jsonable_encoder(application)


@router.put("/{application_id}", response_model=LicenseApplication)
def update_application(
    *,
    db: Session = Depends(get_db),
    application_id: int,
    application_in: LicenseApplicationUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a license application.
    """
    application = crud.license_application.get(db, id=application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License application not found",
        )
    
    # If the status is changing to APPROVED, set the reviewer
    if (application_in.status == ApplicationStatus.APPROVED and
        application.status != ApplicationStatus.APPROVED):
        application_in.reviewed_by = current_user.id
        application_in.review_date = "now()"  # SQLAlchemy will convert this
    
    # Update application
    application = crud.license_application.update(db, db_obj=application, obj_in=application_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(application.id),
            "description": f"User {current_user.username} updated license application {application.id} to {application.status}"
        }
    )
    
    return application


@router.post("/{application_id}/approve", response_model=dict)
def approve_application(
    *,
    db: Session = Depends(get_db),
    application_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Approve a license application and create a license.
    """
    application = crud.license_application.get(db, id=application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License application not found",
        )
    
    # Check if already approved
    if application.status == ApplicationStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application already approved",
        )
    
    # Get citizen
    citizen = crud.citizen.get(db, id=application.citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Update application status
    crud.license_application.update(
        db,
        db_obj=application,
        obj_in={
            "status": ApplicationStatus.APPROVED,
            "reviewed_by": current_user.id,
            "review_date": "now()",
        }
    )
    
    # Create license
    license_number = crud.license.generate_license_number()
    license = crud.license.create(
        db,
        obj_in={
            "license_number": license_number,
            "citizen_id": citizen.id,
            "category": application.applied_category,
            "status": "active",
        }
    )
    
    # Update application with license ID
    crud.license_application.update(
        db,
        db_obj=application,
        obj_in={"approved_license_id": license.id}
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(application.id),
            "description": f"User {current_user.username} approved license application {application.id} and created license {license.license_number}"
        }
    )
    
    # Create transaction
    crud.transaction.create(
        db,
        obj_in={
            "transaction_type": "license_issuance",
            "transaction_ref": crud.transaction.generate_transaction_ref(),
            "status": "completed",
            "user_id": current_user.id,
            "citizen_id": citizen.id,
            "license_id": license.id,
            "application_id": application.id,
            "completed_at": "now()",
            "notes": f"License issued via application approval"
        }
    )
    
    return {
        "message": "Application approved and license created",
        "application_id": application.id,
        "license_id": license.id,
        "license_number": license.license_number
    }


@router.delete("/{application_id}", response_model=LicenseApplication)
def delete_application(
    *,
    db: Session = Depends(get_db),
    application_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a license application (soft delete).
    """
    application = crud.license_application.get(db, id=application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License application not found",
        )
    
    # Soft delete application
    application = crud.license_application.soft_delete(db, id=application_id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.DELETE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(application.id),
            "description": f"User {current_user.username} deleted license application {application.id}"
        }
    )
    
    return application


@router.get("/citizen/{citizen_id}", response_model=List[LicenseApplication])
def read_applications_by_citizen(
    *,
    db: Session = Depends(get_db),
    citizen_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get license applications for a specific citizen.
    """
    # Check if citizen exists
    citizen = crud.citizen.get(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    applications = crud.license_application.get_by_citizen_id(
        db, citizen_id=citizen_id, skip=skip, limit=limit
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.APPLICATION,
            "description": f"User {current_user.username} viewed license applications for citizen {citizen.id_number}"
        }
    )
    
    return applications 