from typing import Any, List, Dict
import logging

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType, TransactionType, TransactionStatus
from app.models.user import User
from app.schemas.license import License, LicenseCreate, LicenseUpdate
from app.services.license_generator import (
    generate_license_qr_code,
    generate_license_barcode_data,
    generate_license_preview,
    generate_sa_license_front,
    generate_sa_license_back,
    generate_watermark_template,
    get_license_specifications
)
from app.services.production_license_generator import production_generator
from app.services.file_manager import file_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[License])
def read_licenses(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    status: str = None,
    license_number: str = None,
    citizen_id_search: str = None,
    citizen_name_search: str = None,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve licenses with optional filtering.
    """
    from sqlalchemy import and_, or_, text
    from app.models.license import License as LicenseModel
    from app.models.citizen import Citizen as CitizenModel
    
    if include_inactive and not (current_user.is_superuser or getattr(current_user, 'is_admin', False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view inactive licenses",
        )
    
    query = db.query(LicenseModel)
    
    # Filter by active/inactive status first
    if not include_inactive:
        query = query.filter(LicenseModel.is_active == True)
    
    # Filter by license status
    if status:
        try:
            from app.models.license import LicenseStatus
            status_enum = LicenseStatus(status)
            query = query.filter(LicenseModel.status == status_enum)
        except (ValueError, AttributeError):
            # Invalid status, ignore this filter
            pass
    
    # Filter by license number
    if license_number:
        query = query.filter(LicenseModel.license_number.ilike(f"%{license_number}%"))
    
    # Filter by citizen ID or name search
    if citizen_id_search or citizen_name_search:
        # Join with citizen table
        query = query.join(CitizenModel, LicenseModel.citizen_id == CitizenModel.id)
        
        if citizen_id_search:
            # Search by citizen ID number or database ID
            if citizen_id_search.isdigit():
                query = query.filter(
                    or_(
                        CitizenModel.id_number.ilike(f"%{citizen_id_search}%"),
                        CitizenModel.id == int(citizen_id_search)
                    )
                )
        
        if citizen_name_search:
            # Search by citizen name (first name or last name)
            name_search = f"%{citizen_name_search}%"
            query = query.filter(
                or_(
                    CitizenModel.first_name.ilike(name_search),
                    CitizenModel.last_name.ilike(name_search),
                    text(f"CONCAT(citizens.first_name, ' ', citizens.last_name) ILIKE '{name_search}'")
                )
            )
    
    # Apply pagination
    licenses = query.offset(skip).limit(limit).all()

    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "description": f"User {current_user.username} retrieved list of licenses with filters: status={status}, license_number={license_number}, citizen_search={citizen_id_search or citizen_name_search}"
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
        "category": license.category.value,
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "status": license.status.value,
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
        "category": license.category.value,
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "status": license.status.value,
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
        "category": license.category.value,
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "status": license.status.value,
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
        "category": license.category.value,
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "status": license.status.value,
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
            "transaction_type": TransactionType.LICENSE_ISSUANCE,
            "transaction_ref": transaction_ref,
            "status": TransactionStatus.COMPLETED,
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


@router.get("/{license_id}/preview/front", response_model=Dict[str, str])
def get_sa_license_front_preview(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a South African driver's license front side preview.
    Uses exact ISO specifications and coordinates.
    Returns a base64 encoded PNG image at 300 DPI.
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
    
    # Prepare license data with all required fields including citizen information
    license_data = {
        "id": license.id,
        "license_number": license.license_number,
        "category": license.category.value,
        "issue_date": license.issue_date.isoformat() if license.issue_date else None,
        "expiry_date": license.expiry_date.isoformat() if license.expiry_date else None,
        "status": license.status.value,
        "restrictions": license.restrictions,
        "medical_conditions": license.medical_conditions,
        "iso_country_code": getattr(license, 'iso_country_code', 'ZAF'),
        "iso_issuing_authority": getattr(license, 'iso_issuing_authority', 'Department of Transport'),
        # Merge citizen fields that the SA generator expects
        "id_number": citizen.id_number,
        "first_name": citizen.first_name,
        "last_name": citizen.last_name,
        "middle_name": getattr(citizen, 'middle_name', ''),
        "date_of_birth": citizen.date_of_birth.isoformat() if citizen.date_of_birth else None,
        "gender": citizen.gender.value if hasattr(citizen.gender, 'value') else str(citizen.gender),
    }
    
    # Generate professional front side preview
    preview = generate_sa_license_front(license_data, citizen.photo_url)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} generated SA front preview for license {license.license_number}"
        }
    )
    
    return {
        "preview": preview,
        "format": "PNG",
        "dpi": "300",
        "dimensions": "1012x638 pixels (85.60x54.00 mm)"
    }


@router.get("/{license_id}/preview/back", response_model=Dict[str, str])
def get_sa_license_back_preview(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a South African driver's license back side preview.
    Uses exact ISO specifications with PDF417 barcode.
    Returns a base64 encoded PNG image at 300 DPI.
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
        "category": license.category.value,
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "status": license.status.value,
        "id_number": citizen.id_number,
        "first_name": citizen.first_name,
        "last_name": citizen.last_name,
        "date_of_birth": citizen.date_of_birth,
        "restrictions": license.restrictions,
        "medical_conditions": license.medical_conditions,
    }
    
    # Generate professional back side preview
    preview = generate_sa_license_back(license_data)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} generated SA back preview for license {license.license_number}"
        }
    )
    
    return {
        "preview": preview,
        "format": "PNG",
        "dpi": "300",
        "dimensions": "1012x638 pixels (85.60x54.00 mm)",
        "features": "PDF417 barcode, fingerprint area, license categories"
    }


@router.get("/watermark-template", response_model=Dict[str, str])
def get_watermark_template(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    width: int = 1012,
    height: int = 638,
    text: str = "SOUTH AFRICA"
) -> Any:
    """
    Generate a watermark template for license printing.
    Uses exact ISO specifications and dimensions.
    Returns a base64 encoded PNG image of the watermark pattern.
    """
    # Generate professional watermark template
    watermark = generate_watermark_template(width, height, text)
    
    # Log action (no specific license, so no resource_id)
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "description": f"User {current_user.username} generated watermark template ({width}x{height})"
        }
    )
    
    return {
        "watermark": watermark,
        "dimensions": f"{width}x{height}",
        "text": text,
        "format": "PNG",
        "dpi": "300",
        "specifications": "ISO/IEC 18013-1 compliant"
    }


@router.get("/specifications", response_model=Dict[str, Any])
def get_license_specifications_endpoint(
    *,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get detailed license specifications, coordinates, and technical details.
    Useful for developers and integration purposes.
    """
    return get_license_specifications()


@router.post("/{license_id}/generate", response_model=Dict[str, Any])
def generate_license_files(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    background_tasks: BackgroundTasks,
    force_regenerate: bool = False,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate license files with photo (front, back, combined PDF).
    This creates production-ready files stored on the server.
    """
    try:
        # Get license with citizen
        license = crud.license.get(db, id=license_id)
        if not license:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License not found",
            )
        
        # Get citizen with photo information
        citizen = crud.citizen.get(db, id=license.citizen_id)
        if not citizen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Citizen not found",
            )
        
        # Check if citizen has a photo
        if not citizen.photo_url:
            logger.warning(f"Citizen {citizen.id} has no photo URL")
            # You could either:
            # 1. Raise an error requiring photo upload first
            # raise HTTPException(
            #     status_code=status.HTTP_400_BAD_REQUEST,
            #     detail="Citizen photo is required before generating license. Please upload a photo first.",
            # )
            # 2. Or continue with placeholder (current behavior)
        
        # Prepare license data with all required fields including citizen information
        license_data = {
            "id": license.id,
            "license_number": license.license_number,
            "category": license.category.value,
            "issue_date": license.issue_date.isoformat() if license.issue_date else None,
            "expiry_date": license.expiry_date.isoformat() if license.expiry_date else None,
            "status": license.status.value,
            "restrictions": license.restrictions,
            "medical_conditions": license.medical_conditions,
            "iso_country_code": getattr(license, 'iso_country_code', 'ZAF'),
            "iso_issuing_authority": getattr(license, 'iso_issuing_authority', 'Department of Transport'),
            # Merge citizen fields that the SA generator expects
            "id_number": citizen.id_number,
            "first_name": citizen.first_name,
            "last_name": citizen.last_name,
            "middle_name": getattr(citizen, 'middle_name', ''),
            "date_of_birth": citizen.date_of_birth.isoformat() if citizen.date_of_birth else None,
            "gender": citizen.gender.value if hasattr(citizen.gender, 'value') else str(citizen.gender),
        }
        
        # Prepare citizen data ensuring we have the photo URL
        citizen_data = {
            "id": citizen.id,
            "id_number": citizen.id_number,
            "first_name": citizen.first_name,
            "last_name": citizen.last_name,
            "middle_name": getattr(citizen, 'middle_name', ''),
            "date_of_birth": citizen.date_of_birth.isoformat() if citizen.date_of_birth else None,
            "gender": citizen.gender,
            "nationality": getattr(citizen, 'nationality', 'South African'),
            "photo_url": citizen.photo_url,  # This might be None
            "processed_photo_path": getattr(citizen, 'processed_photo_path', None),
        }
        
        logger.info(f"Generating license files for license {license_id} with citizen photo: {citizen.photo_url}")
        
        # Generate complete license package
        result = production_generator.generate_complete_license(
            license_data, citizen_data, force_regenerate
        )
        
        # Update database with file paths
        crud.license.update_file_paths(db, license_id=license_id, file_paths=result)
        
        # Update citizen photo paths if they were processed
        if "processed_photo_path" in result:
            crud.citizen.update_photo_paths(
                db, 
                citizen_id=citizen.id,
                processed_photo_path=result["processed_photo_path"]
            )
        
        # Add cleanup task in background
        background_tasks.add_task(file_manager.cleanup_temp_files, 1)
        
        # Log action
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.GENERATE,
                "resource_type": ResourceType.LICENSE,
                "resource_id": str(license.id),
                "description": f"User {current_user.username} generated files for license {license.license_number}"
            }
        )
        
        return {
            "message": "License files generated successfully",
            "license_id": license_id,
            "license_number": license.license_number,
            "files": result,
            "cached": result.get("from_cache", False)
        }
        
    except Exception as e:
        logger.error(f"Error generating license files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating license files: {str(e)}"
        )


@router.get("/{license_id}/files", response_model=Dict[str, Any])
def get_license_files(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get information about generated license files
    """
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    files_info = {}
    
    # Check which files exist and get their info
    file_fields = [
        "front_image_path", "back_image_path", "watermark_image_path",
        "front_pdf_path", "back_pdf_path", "watermark_pdf_path", "combined_pdf_path"
    ]
    
    for field in file_fields:
        path = getattr(license, field, None)
        if path and file_manager.file_exists(path):
            files_info[field] = {
                "path": path,
                "url": file_manager.get_file_url(path),
                "size_bytes": file_manager.get_file_size(path),
                "exists": True
            }
        else:
            files_info[field] = {
                "path": path,
                "url": None,
                "size_bytes": 0,
                "exists": False
            }
    
    return {
        "license_id": license_id,
        "license_number": license.license_number,
        "last_generated": license.last_generated,
        "generation_version": license.generation_version,
        "files": files_info
    }


@router.get("/{license_id}/download/{file_type}")
def download_license_file(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    file_type: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Download a specific license file
    """
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Map file types to database fields
    file_mapping = {
        "front_image": "front_image_path",
        "back_image": "back_image_path",
        "watermark_image": "watermark_image_path",
        "front_pdf": "front_pdf_path", 
        "back_pdf": "back_pdf_path",
        "watermark_pdf": "watermark_pdf_path",
        "combined_pdf": "combined_pdf_path"
    }
    
    if file_type not in file_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Supported types: {list(file_mapping.keys())}"
        )
    
    file_path = getattr(license, file_mapping[file_type], None)
    if not file_path or not file_manager.file_exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found. Generate license files first."
        )
    
    # Get full file path
    full_path = file_manager.base_dir / file_path
    
    # Determine media type
    media_type = "application/pdf" if file_type.endswith("_pdf") else "image/png"
    
    # Create filename for download
    extension = "pdf" if file_type.endswith("_pdf") else "png"
    filename = f"license_{license.license_number}_{file_type}.{extension}"
    
    # Log download
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"User {current_user.username} downloaded {file_type} for license {license.license_number}"
        }
    )
    
    return FileResponse(
        path=str(full_path),
        media_type=media_type,
        filename=filename
    )


@router.post("/{license_id}/photo/update", response_model=Dict[str, Any])
def update_license_photo(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    photo_url: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update the photo for a license holder and reprocess
    """
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
    
    try:
        # Update photo URL in database
        crud.citizen.update(db, db_obj=citizen, obj_in={"photo_url": photo_url})
        
        # Process new photo
        original_path, processed_path = production_generator.update_citizen_photo(
            citizen.id, photo_url
        )
        
        # Update citizen with new photo paths
        crud.citizen.update_photo_paths(
            db,
            citizen_id=citizen.id,
            stored_photo_path=original_path,
            processed_photo_path=processed_path
        )
        
        # Mark license for regeneration
        crud.license.mark_for_regeneration(db, license_id=license_id)
        
        # Add background cleanup task
        background_tasks.add_task(file_manager.cleanup_temp_files, 1)
        
        # Log action
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.UPDATE,
                "resource_type": ResourceType.LICENSE,
                "resource_id": str(license.id),
                "description": f"User {current_user.username} updated photo for license {license.license_number}"
            }
        )
        
        return {
            "message": "Photo updated successfully",
            "license_id": license_id,
            "citizen_id": citizen.id,
            "original_photo_path": original_path,
            "processed_photo_path": processed_path,
            "regeneration_required": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating photo: {str(e)}"
        )


@router.get("/storage/stats", response_model=Dict[str, Any])
def get_storage_statistics(
    *,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get storage system statistics
    """
    try:
        stats = file_manager.get_storage_stats()
        
        # Convert bytes to human readable format
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} TB"
        
        formatted_stats = {
            **stats,
            "total_size_formatted": format_bytes(stats["total_size_bytes"]),
            "license_size_formatted": format_bytes(stats["license_size_bytes"]),
            "photo_size_formatted": format_bytes(stats["photo_size_bytes"]),
            "temp_size_formatted": format_bytes(stats["temp_size_bytes"]),
        }
        
        return formatted_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting storage stats: {str(e)}"
        )


@router.post("/storage/cleanup", response_model=Dict[str, str])
def cleanup_storage(
    *,
    background_tasks: BackgroundTasks,
    older_than_hours: int = 24,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Trigger storage cleanup for temporary files
    """
    try:
        # Add cleanup task to background
        background_tasks.add_task(file_manager.cleanup_temp_files, older_than_hours)
        
        return {
            "message": f"Storage cleanup initiated for files older than {older_than_hours} hours",
            "status": "running"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating cleanup: {str(e)}"
        ) 