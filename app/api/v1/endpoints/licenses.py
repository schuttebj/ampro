from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType
from app.models.user import User
from app.schemas.license import License, LicenseCreate, LicenseUpdate
from app.services.license_generator import (
    generate_license_qr_code,
    generate_license_barcode_data,
    generate_license_preview
)

router = APIRouter()


@router.get("/", response_model=List[License])
def read_licenses(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve licenses.
    """
    licenses = crud.license.get_multi(db, skip=skip, limit=limit)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "description": f"User {current_user.username} retrieved list of licenses"
        }
    )
    
    return licenses


@router.post("/", response_model=License)
def create_license(
    *,
    db: Session = Depends(get_db),
    license_in: LicenseCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new license.
    """
    # Check if citizen exists
    citizen = crud.citizen.get(db, id=license_in.citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Check if license number already exists
    existing_license = crud.license.get_by_license_number(db, license_number=license_in.license_number)
    if existing_license:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A license with this number already exists",
        )
    
    # Create license
    license = crud.license.create(db, obj_in=license_in)
    
    # Create barcode data
    barcode_data = generate_license_barcode_data(license.license_number, citizen.id_number)
    
    # Update license with barcode data
    crud.license.update(db, db_obj=license, obj_in={"barcode_data": barcode_data})
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} created license {license.license_number}"
        }
    )
    
    return license


@router.get("/generate-number", response_model=dict)
def generate_license_number(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a unique license number.
    """
    license_number = crud.license.generate_license_number()
    return {"license_number": license_number}


@router.get("/number/{license_number}", response_model=Dict[str, Any])
def read_license_by_number(
    *,
    db: Session = Depends(get_db),
    license_number: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get license by license number.
    """
    license = crud.license.get_by_license_number(db, license_number=license_number)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Get related citizen
    citizen = crud.citizen.get(db, id=license.citizen_id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} viewed license {license.license_number}"
        }
    )
    
    # Build response with explicit dictionary creation
    license_data = {
        "id": license.id,
        "license_number": license.license_number,
        "citizen_id": license.citizen_id,
        "category": str(license.category),
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "status": str(license.status),
        "restrictions": license.restrictions,
        "medical_conditions": license.medical_conditions,
        "file_url": license.file_url,
        "barcode_data": license.barcode_data,
        "is_active": license.is_active,
        "created_at": license.created_at,
        "updated_at": license.updated_at
    }
    
    # Include citizen data
    citizen_data = None
    if citizen:
        citizen_data = {
            "id": citizen.id,
            "id_number": citizen.id_number,
            "first_name": citizen.first_name,
            "last_name": citizen.last_name,
            "date_of_birth": citizen.date_of_birth
        }
    
    return {
        "license": license_data,
        "citizen": citizen_data
    }


@router.get("/{license_id}", response_model=Dict[str, Any])
def read_license(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get license by ID.
    """
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Get related citizen
    citizen = crud.citizen.get(db, id=license.citizen_id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} viewed license {license.license_number}"
        }
    )
    
    # Build response with explicit dictionary creation
    license_data = {
        "id": license.id,
        "license_number": license.license_number,
        "citizen_id": license.citizen_id,
        "category": str(license.category),
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "status": str(license.status),
        "restrictions": license.restrictions,
        "medical_conditions": license.medical_conditions,
        "file_url": license.file_url,
        "barcode_data": license.barcode_data,
        "is_active": license.is_active,
        "created_at": license.created_at,
        "updated_at": license.updated_at
    }
    
    # Include citizen data
    citizen_data = None
    if citizen:
        citizen_data = {
            "id": citizen.id,
            "id_number": citizen.id_number,
            "first_name": citizen.first_name,
            "last_name": citizen.last_name,
            "date_of_birth": citizen.date_of_birth
        }
    
    return {
        "license": license_data,
        "citizen": citizen_data
    }


@router.put("/{license_id}", response_model=License)
def update_license(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    license_in: LicenseUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a license.
    """
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Update license
    license = crud.license.update(db, db_obj=license, obj_in=license_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} updated license {license.license_number}"
        }
    )
    
    return license


@router.delete("/{license_id}", response_model=License)
def delete_license(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a license (soft delete).
    """
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Soft delete license
    license = crud.license.soft_delete(db, id=license_id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.DELETE,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} deleted license {license.license_number}"
        }
    )
    
    return license


@router.get("/{license_id}/qr-code", response_model=Dict[str, str])
def get_license_qr_code(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a QR code for a license.
    Returns a base64 encoded PNG image.
    """
    # Get license with citizen
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    citizen = crud.citizen.get(db, id=license.citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Prepare license data
    license_data = {
        "license_number": license.license_number,
        "category": str(license.category),
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "status": str(license.status),
        "id_number": citizen.id_number,
        "first_name": citizen.first_name,
        "last_name": citizen.last_name,
    }
    
    # Generate QR code
    qr_code = generate_license_qr_code(license_data)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} generated QR code for license {license.license_number}"
        }
    )
    
    return {"qr_code": qr_code}


@router.get("/{license_id}/preview", response_model=Dict[str, str])
def get_license_preview(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a preview image of a license.
    Returns a base64 encoded PNG image.
    """
    # Get license with citizen
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    citizen = crud.citizen.get(db, id=license.citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Prepare license data
    license_data = {
        "license_number": license.license_number,
        "category": str(license.category),
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "status": str(license.status),
        "id_number": citizen.id_number,
        "first_name": citizen.first_name,
        "last_name": citizen.last_name,
        "date_of_birth": citizen.date_of_birth,
        "restrictions": license.restrictions,
        "medical_conditions": license.medical_conditions,
    }
    
    # Generate preview
    preview = generate_license_preview(license_data, citizen.photo_url)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} generated preview for license {license.license_number}"
        }
    )
    
    return {"preview": preview}


@router.post("/{license_id}/print", response_model=Dict[str, Any])
def print_license(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Print a license. This simulates sending the license to a printer.
    In a real system, this would communicate with a license printer.
    """
    # Get license
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Get citizen
    citizen = crud.citizen.get(db, id=license.citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Generate a transaction record
    transaction_ref = crud.transaction.generate_transaction_ref()
    transaction = crud.transaction.create(
        db,
        obj_in={
            "transaction_type": "license_issuance",
            "transaction_ref": transaction_ref,
            "status": "completed",
            "user_id": current_user.id,
            "citizen_id": citizen.id,
            "license_id": license.id,
            "completed_at": "now()",
            "notes": f"License printed for {citizen.first_name} {citizen.last_name}",
            "amount": 12000,  # Amount in cents (R120)
        }
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.PRINT,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} printed license {license.license_number}"
        }
    )
    
    # Return success response with transaction details
    return {
        "success": True,
        "message": "License sent to printer",
        "transaction_id": transaction.id,
        "transaction_ref": transaction.transaction_ref,
        "amount": "R120.00"
    } 