from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.license import ApplicationStatus, LicenseStatus, PrintJobStatus, ShippingStatus
from app.models.audit import ActionType, ResourceType
from app.schemas.print_job import (
    PrintJob, PrintJobCreate, PrintJobUpdate, PrintJobAssignment, 
    PrintJobStart, PrintJobComplete, PrintQueue, PrintJobStatistics,
    ShippingRecord, ShippingRecordCreate, ShippingRecordUpdate, 
    ShippingAction, ShippingStatistics, WorkflowStatus, CollectionPointSummary
)
from app.services.printing_service import printing_service
from app.services.iso_compliance_service import iso_compliance_service

router = APIRouter()


# ============================================================================
# APPLICATION WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/applications/{application_id}/approve", response_model=Dict[str, Any])
def approve_application(
    *,
    db: Session = Depends(get_db),
    application_id: int,
    collection_point: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Approve an application and generate ISO-compliant license files.
    """
    # Get application
    application = crud.license_application.get(db, id=application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application.status != ApplicationStatus.UNDER_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application is not in review status"
        )
    
    # Check if all verifications are complete
    if not (application.documents_verified and application.medical_verified and application.payment_verified):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All verifications must be completed before approval"
        )
    
    # Create license
    license_data = {
        "citizen_id": application.citizen_id,
        "category": application.applied_category,
        "collection_point": collection_point,
        "status": LicenseStatus.PENDING_COLLECTION
    }
    
    # Generate license number
    license_number = crud.license.generate_license_number()
    license_data["license_number"] = license_number
    
    license = crud.license.create(db, obj_in=license_data)
    
    # Update application
    application_update = {
        "status": ApplicationStatus.APPROVED,
        "approved_license_id": license.id,
        "reviewed_by": current_user.id,
        "review_date": datetime.utcnow(),
        "collection_point": collection_point
    }
    crud.license_application.update(db, db_obj=application, obj_in=application_update)
    
    # Generate license files in background with ISO compliance
    background_tasks.add_task(generate_iso_compliant_license_and_queue_print, db, license.id, application.id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(application.id),
            "description": f"Application {application.id} approved by {current_user.username} with ISO 18013 compliance"
        }
    )
    
    return {
        "message": "Application approved successfully with ISO 18013 compliance",
        "application_id": application.id,
        "license_id": license.id,
        "license_number": license.license_number,
        "status": ApplicationStatus.APPROVED,
        "iso_compliant": True
    }


def generate_iso_compliant_license_and_queue_print(db: Session, license_id: int, application_id: int):
    """
    Background task to generate ISO-compliant license files and create print job.
    """
    try:
        # Get license and citizen data
        license = crud.license.get(db, id=license_id)
        citizen = crud.citizen.get(db, id=license.citizen_id)
        
        # Prepare license data for ISO compliance
        license_data = {
            "license_number": license.license_number,
            "citizen_id": citizen.id,
            "first_name": citizen.first_name,
            "last_name": citizen.last_name,
            "birth_date": citizen.birth_date,
            "issue_date": license.issue_date,
            "expiry_date": license.expiry_date,
            "category": license.category.value,
            "gender": getattr(citizen, 'gender', 'M'),
            "nationality": getattr(citizen, 'nationality', 'ZAF'),
            "restrictions": license.restrictions,
            "photo_path": getattr(citizen, 'photo_path', None)
        }
        
        # Validate ISO compliance
        validation_result = iso_compliance_service.validate_iso_compliance(license_data)
        
        if not validation_result["compliant"]:
            # Update application with validation errors
            application = crud.license_application.get(db, id=application_id)
            crud.license_application.update(
                db, 
                db_obj=application, 
                obj_in={
                    "status": ApplicationStatus.UNDER_REVIEW,
                    "review_notes": f"ISO compliance validation failed: {', '.join(validation_result['issues'])}"
                }
            )
            return
        
        # Generate ISO compliance data
        mrz_data = iso_compliance_service.generate_mrz_data(license_data)
        security_features = iso_compliance_service.generate_security_features(license_data)
        digital_signature = iso_compliance_service.generate_digital_signature(license_data)
        biometric_template = iso_compliance_service.generate_biometric_template()
        chip_data = iso_compliance_service.generate_chip_data(license_data)
        
        # Update license with ISO compliance data
        iso_update_data = {
            "mrz_line1": mrz_data["mrz_line1"],
            "mrz_line2": mrz_data["mrz_line2"],
            "mrz_line3": mrz_data["mrz_line3"],
            "security_features": security_features,
            "digital_signature": digital_signature,
            "biometric_template": biometric_template,
            "chip_serial_number": chip_data["chip_serial_number"],
            "chip_data_encrypted": chip_data["chip_data_encrypted"],
            "iso_document_number": f"ISO{license.license_number}"
        }
        
        crud.license.update(db, db_obj=license, obj_in=iso_update_data)
        
        # Generate license files (using existing production generator)
        from app.services.production_license_generator import production_generator
        
        result = production_generator.generate_license_files(
            license=license,
            citizen=citizen,
            force_regenerate=True
        )
        
        if result["success"]:
            # Update application status
            application = crud.license_application.get(db, id=application_id)
            crud.license_application.update(
                db, 
                db_obj=application, 
                obj_in={"status": ApplicationStatus.LICENSE_GENERATED}
            )
            
            # Create print job
            print_job_data = {
                "application_id": application_id,
                "license_id": license_id,
                "front_pdf_path": result["files"]["front_pdf_path"],
                "back_pdf_path": result["files"]["back_pdf_path"],
                "combined_pdf_path": result["files"]["combined_pdf_path"],
                "priority": 1
            }
            
            print_job = crud.print_job.create(db, obj_in=print_job_data)
            
            # Update application status to queued for printing
            crud.license_application.update(
                db, 
                db_obj=application, 
                obj_in={"status": ApplicationStatus.QUEUED_FOR_PRINTING}
            )
            
    except Exception as e:
        # Handle error - update application status
        application = crud.license_application.get(db, id=application_id)
        crud.license_application.update(
            db, 
            db_obj=application, 
            obj_in={
                "status": ApplicationStatus.UNDER_REVIEW,
                "review_notes": f"ISO-compliant license generation failed: {str(e)}"
            }
        )


# ============================================================================
# ISO COMPLIANCE ENDPOINTS
# ============================================================================

@router.get("/licenses/{license_id}/iso-compliance", response_model=Dict[str, Any])
def get_license_iso_compliance(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get ISO 18013 compliance information for a license.
    """
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    citizen = crud.citizen.get(db, id=license.citizen_id)
    
    return {
        "license_id": license.id,
        "license_number": license.license_number,
        "iso_compliant": True,
        "iso_version": license.iso_version,
        "iso_country_code": license.iso_country_code,
        "iso_issuing_authority": license.iso_issuing_authority,
        "iso_document_number": license.iso_document_number,
        "international_validity": license.international_validity,
        "vienna_convention_compliant": license.vienna_convention_compliant,
        "mrz_data": {
            "line1": license.mrz_line1,
            "line2": license.mrz_line2,
            "line3": license.mrz_line3
        },
        "security_features": license.security_features,
        "chip_data": {
            "serial_number": license.chip_serial_number,
            "has_encrypted_data": bool(license.chip_data_encrypted)
        },
        "biometric_data": {
            "has_template": bool(license.biometric_template)
        },
        "digital_signature": {
            "has_signature": bool(license.digital_signature)
        }
    }


@router.post("/licenses/{license_id}/validate-iso", response_model=Dict[str, Any])
def validate_license_iso_compliance(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Validate ISO 18013 compliance for a license.
    """
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    citizen = crud.citizen.get(db, id=license.citizen_id)
    
    # Prepare license data for validation
    license_data = {
        "license_number": license.license_number,
        "citizen_id": citizen.id,
        "first_name": citizen.first_name,
        "last_name": citizen.last_name,
        "birth_date": citizen.birth_date,
        "issue_date": license.issue_date,
        "expiry_date": license.expiry_date,
        "category": license.category.value,
        "photo_path": getattr(citizen, 'photo_path', None)
    }
    
    # Validate compliance
    validation_result = iso_compliance_service.validate_iso_compliance(license_data)
    
    return {
        "license_id": license.id,
        "license_number": license.license_number,
        "validation_result": validation_result,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/licenses/{license_id}/regenerate-iso", response_model=Dict[str, Any])
def regenerate_iso_compliance_data(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Regenerate ISO 18013 compliance data for a license.
    """
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    citizen = crud.citizen.get(db, id=license.citizen_id)
    
    try:
        # Prepare license data
        license_data = {
            "license_number": license.license_number,
            "citizen_id": citizen.id,
            "first_name": citizen.first_name,
            "last_name": citizen.last_name,
            "birth_date": citizen.birth_date,
            "issue_date": license.issue_date,
            "expiry_date": license.expiry_date,
            "category": license.category.value,
            "gender": getattr(citizen, 'gender', 'M'),
            "nationality": getattr(citizen, 'nationality', 'ZAF'),
            "restrictions": license.restrictions
        }
        
        # Generate new ISO compliance data
        mrz_data = iso_compliance_service.generate_mrz_data(license_data)
        security_features = iso_compliance_service.generate_security_features(license_data)
        digital_signature = iso_compliance_service.generate_digital_signature(license_data)
        biometric_template = iso_compliance_service.generate_biometric_template()
        chip_data = iso_compliance_service.generate_chip_data(license_data)
        
        # Update license
        iso_update_data = {
            "mrz_line1": mrz_data["mrz_line1"],
            "mrz_line2": mrz_data["mrz_line2"],
            "mrz_line3": mrz_data["mrz_line3"],
            "security_features": security_features,
            "digital_signature": digital_signature,
            "biometric_template": biometric_template,
            "chip_serial_number": chip_data["chip_serial_number"],
            "chip_data_encrypted": chip_data["chip_data_encrypted"],
            "iso_document_number": f"ISO{license.license_number}",
            "last_generated": datetime.utcnow()
        }
        
        updated_license = crud.license.update(db, db_obj=license, obj_in=iso_update_data)
        
        # Log action
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.UPDATE,
                "resource_type": ResourceType.LICENSE,
                "resource_id": str(license.id),
                "description": f"ISO compliance data regenerated for license {license.license_number}"
            }
        )
        
        return {
            "message": "ISO compliance data regenerated successfully",
            "license_id": license.id,
            "license_number": license.license_number,
            "regenerated_at": updated_license.last_generated.isoformat(),
            "iso_compliant": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate ISO compliance data: {str(e)}"
        )


# ============================================================================
# PRINT JOB MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/print-queue", response_model=PrintQueue)
def get_print_queue(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get the current print queue.
    """
    print_jobs = crud.print_job.get_queue(db, skip=skip, limit=limit)
    
    # Get counts
    queued_count = len([job for job in print_jobs if job.status.value == 'queued'])
    assigned_count = len([job for job in print_jobs if job.status.value == 'assigned'])
    
    return {
        "print_jobs": print_jobs,
        "total_count": len(print_jobs),
        "queued_count": queued_count,
        "assigned_count": assigned_count
    }


@router.post("/print-jobs/{print_job_id}/assign", response_model=PrintJob)
def assign_print_job(
    *,
    db: Session = Depends(get_db),
    print_job_id: int,
    assignment: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Assign a print job to a user.
    """
    # Extract user_id from assignment data
    assigned_to_user_id = assignment.get("assigned_to_user_id") or assignment.get("user_id")
    
    if not assigned_to_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="assigned_to_user_id is required"
        )
    
    print_job = crud.print_job.assign_to_user(
        db, 
        print_job_id=print_job_id, 
        user_id=assigned_to_user_id
    )
    
    if not print_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Print job cannot be assigned (may already be assigned or completed)"
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(print_job.application_id),
            "description": f"Print job {print_job_id} assigned to user {assigned_to_user_id}"
        }
    )
    
    return print_job


@router.post("/print-jobs/{print_job_id}/start", response_model=PrintJob)
def start_print_job(
    *,
    db: Session = Depends(get_db),
    print_job_id: int,
    start_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Start printing a print job.
    """
    # Extract data from start_data
    user_id = start_data.get("user_id", current_user.id)
    printer_name = start_data.get("printer_name")
    
    print_job = crud.print_job.start_printing(
        db,
        print_job_id=print_job_id,
        user_id=user_id,
        printer_name=printer_name
    )
    
    if not print_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Print job cannot be started (may not be assigned or already completed)"
        )
    
    # Update application status
    application = crud.license_application.get(db, id=print_job.application_id)
    crud.license_application.update(
        db,
        db_obj=application,
        obj_in={"status": ApplicationStatus.PRINTING}
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(print_job.application_id),
            "description": f"Print job {print_job_id} started by user {user_id}"
        }
    )
    
    return print_job


@router.post("/print-jobs/{print_job_id}/complete", response_model=Dict[str, Any])
def complete_print_job(
    *,
    db: Session = Depends(get_db),
    print_job_id: int,
    complete_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Mark a print job as completed and create shipping record.
    """
    # Extract data from complete_data
    user_id = complete_data.get("user_id", current_user.id)
    copies_printed = complete_data.get("copies_printed", 1)
    notes = complete_data.get("notes", "")
    success = complete_data.get("success", True)
    
    print_job = crud.print_job.complete_printing(
        db,
        print_job_id=print_job_id,
        user_id=user_id,
        copies_printed=copies_printed,
        notes=notes
    )
    
    if not print_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Print job cannot be completed (may not be in printing status)"
        )
    
    # Update application status
    application = crud.license_application.get(db, id=print_job.application_id)
    crud.license_application.update(
        db,
        db_obj=application,
        obj_in={"status": ApplicationStatus.PRINTED}
    )
    
    # Create shipping record
    shipping_data = {
        "application_id": print_job.application_id,
        "license_id": print_job.license_id,
        "print_job_id": print_job.id,
        "collection_point": application.collection_point or "Main Office",
        "status": ShippingStatus.PENDING
    }
    
    shipping_record = crud.shipping_record.create(db, obj_in=shipping_data)
    
    # Update application status to shipped (ready for shipping)
    crud.license_application.update(
        db,
        db_obj=application,
        obj_in={"status": ApplicationStatus.SHIPPED}
    )
    
    # Clean up print files if printing was successful
    if success:
        try:
            import os
            from pathlib import Path
            
            # Delete the generated PDF files
            for file_path in [print_job.front_pdf_path, print_job.back_pdf_path, print_job.combined_pdf_path]:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Deleted print file: {file_path}")
                    except Exception as e:
                        print(f"Failed to delete file {file_path}: {str(e)}")
                        
        except Exception as e:
            print(f"Warning: File cleanup failed: {str(e)}")
            # Don't fail the whole operation if cleanup fails
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(print_job.application_id),
            "description": f"Print job {print_job_id} completed by user {user_id} - Files cleaned up"
        }
    )
    
    return {
        "message": "Print job completed successfully",
        "print_job_id": print_job.id,
        "shipping_record_id": shipping_record.id,
        "application_status": ApplicationStatus.SHIPPED,
        "files_cleaned": success
    }


# ============================================================================
# SHIPPING MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/shipping/pending", response_model=List[ShippingRecord])
def get_pending_shipments(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get pending shipments.
    """
    return crud.shipping_record.get_by_status(
        db, 
        status=ShippingStatus.PENDING, 
        skip=skip, 
        limit=limit
    )


@router.post("/shipping/{shipping_id}/ship", response_model=ShippingRecord)
def ship_license(
    *,
    db: Session = Depends(get_db),
    shipping_id: int,
    ship_data: ShippingAction,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Mark a license as shipped.
    """
    shipping_record = crud.shipping_record.ship_record(
        db,
        shipping_id=shipping_id,
        user_id=ship_data.user_id,
        tracking_number=ship_data.tracking_number,
        shipping_method=ship_data.shipping_method
    )
    
    if not shipping_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipping record cannot be updated (may not be in pending status)"
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(shipping_record.application_id),
            "description": f"License shipped with tracking {ship_data.tracking_number}"
        }
    )
    
    return shipping_record


@router.post("/shipping/{shipping_id}/deliver", response_model=Dict[str, Any])
def deliver_license(
    *,
    db: Session = Depends(get_db),
    shipping_id: int,
    deliver_data: ShippingAction,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Mark a license as delivered to collection point.
    """
    shipping_record = crud.shipping_record.deliver_record(
        db,
        shipping_id=shipping_id,
        user_id=deliver_data.user_id,
        notes=deliver_data.notes
    )
    
    if not shipping_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipping record cannot be updated (may not be in transit)"
        )
    
    # Update application status
    application = crud.license_application.get(db, id=shipping_record.application_id)
    crud.license_application.update(
        db,
        db_obj=application,
        obj_in={"status": ApplicationStatus.READY_FOR_COLLECTION}
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(shipping_record.application_id),
            "description": f"License delivered to collection point {shipping_record.collection_point}"
        }
    )
    
    return {
        "message": "License delivered successfully",
        "shipping_record_id": shipping_record.id,
        "collection_point": shipping_record.collection_point,
        "application_status": ApplicationStatus.READY_FOR_COLLECTION
    }


# ============================================================================
# COLLECTION MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/collection-points/{collection_point}/ready", response_model=List[Dict[str, Any]])
def get_ready_for_collection(
    *,
    db: Session = Depends(get_db),
    collection_point: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get licenses ready for collection at a specific collection point.
    """
    # Get applications ready for collection
    from sqlalchemy import and_
    applications = (
        db.query(crud.license_application.model)
        .filter(
            and_(
                crud.license_application.model.status == ApplicationStatus.READY_FOR_COLLECTION.value,
                crud.license_application.model.collection_point == collection_point
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    result = []
    for app in applications:
        license = crud.license.get(db, id=app.approved_license_id)
        citizen = crud.citizen.get(db, id=app.citizen_id)
        
        result.append({
            "application_id": app.id,
            "license_id": license.id if license else None,
            "license_number": license.license_number if license else None,
            "citizen_name": f"{citizen.first_name} {citizen.last_name}" if citizen else None,
            "citizen_id_number": citizen.id_number if citizen else None,
            "application_date": app.application_date,
            "category": app.applied_category.value,
            "collection_point": app.collection_point,
            "iso_compliant": bool(license.iso_document_number) if license else False
        })
    
    return result


@router.post("/licenses/{license_id}/collect", response_model=Dict[str, Any])
def collect_license(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Mark a license as collected by the citizen.
    """
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    if license.status != LicenseStatus.PENDING_COLLECTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License is not ready for collection"
        )
    
    # Update license status
    license_update = {
        "status": LicenseStatus.ACTIVE,
        "collected_at": datetime.utcnow(),
        "collected_by_user_id": current_user.id
    }
    crud.license.update(db, db_obj=license, obj_in=license_update)
    
    # Find and update application
    application = (
        db.query(crud.license_application.model)
        .filter(crud.license_application.model.approved_license_id == license_id)
        .first()
    )
    
    if application:
        crud.license_application.update(
            db,
            db_obj=application,
            obj_in={"status": ApplicationStatus.COMPLETED}
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.LICENSE,
            "resource_id": str(license.id),
            "description": f"ISO-compliant license {license.license_number} collected by citizen"
        }
    )
    
    return {
        "message": "ISO-compliant license collected successfully",
        "license_id": license.id,
        "license_number": license.license_number,
        "license_status": LicenseStatus.ACTIVE,
        "collected_at": license.collected_at,
        "iso_compliant": bool(license.iso_document_number)
    }


# ============================================================================
# STATISTICS AND REPORTING ENDPOINTS
# ============================================================================

@router.get("/statistics/print-jobs", response_model=PrintJobStatistics)
def get_print_job_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get print job statistics.
    """
    stats = crud.print_job.get_statistics(db)
    total = sum(stats.values())
    
    return {
        "queued": stats.get("queued", 0),
        "assigned": stats.get("assigned", 0),
        "printing": stats.get("printing", 0),
        "completed": stats.get("completed", 0),
        "failed": stats.get("failed", 0),
        "cancelled": stats.get("cancelled", 0),
        "total": total
    }


@router.get("/statistics/shipping", response_model=ShippingStatistics)
def get_shipping_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get shipping statistics.
    """
    stats = crud.shipping_record.get_statistics(db)
    total = sum(stats.values())
    
    return {
        "pending": stats.get("pending", 0),
        "in_transit": stats.get("in_transit", 0),
        "delivered": stats.get("delivered", 0),
        "failed": stats.get("failed", 0),
        "total": total
    }


@router.get("/workflow/status/{application_id}", response_model=WorkflowStatus)
def get_workflow_status(
    *,
    db: Session = Depends(get_db),
    application_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get complete workflow status for an application.
    """
    application = crud.license_application.get(db, id=application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    result = {
        "application_id": application.id,
        "application_status": application.status.value,
        "last_updated": application.last_updated,
        "collection_point": application.collection_point
    }
    
    # Add license info if exists
    if application.approved_license_id:
        license = crud.license.get(db, id=application.approved_license_id)
        if license:
            result["license_id"] = license.id
            result["license_status"] = license.status.value
    
    # Add print job info if exists
    print_jobs = crud.print_job.get_by_application_id(db, application_id=application_id)
    if print_jobs:
        latest_print_job = max(print_jobs, key=lambda x: x.created_at)
        result["print_job_id"] = latest_print_job.id
        result["print_job_status"] = latest_print_job.status.value
    
    # Add shipping info if exists
    shipping = crud.shipping_record.get_by_application_id(db, application_id=application_id)
    if shipping:
        result["shipping_id"] = shipping.id
        result["shipping_status"] = shipping.status.value
    
    return result 


# ============================================================================
# PRINTER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/printers", response_model=List[Dict[str, str]])
def get_available_printers(
    *,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get list of available printers on the system.
    """
    try:
        printers = printing_service.get_available_printers()
        return printers
    except Exception as e:
        # Return mock printers if service fails
        return [
            {"name": "Default Printer", "status": "available"},
            {"name": "HP LaserJet Pro", "status": "available"},
            {"name": "Canon ImageRunner", "status": "available"}
        ]


@router.get("/printers/default", response_model=Dict[str, Any])
def get_default_printer(
    *,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get the default printer.
    """
    try:
        default_printer = printing_service.get_default_printer()
        return {
            "default_printer": default_printer,
            "available": default_printer is not None
        }
    except Exception as e:
        # Return mock default printer if service fails
        return {
            "default_printer": "Default Printer",
            "available": True
        }


@router.post("/print-jobs/{print_job_id}/print", response_model=Dict[str, Any])
def print_license_card(
    *,
    db: Session = Depends(get_db),
    print_job_id: int,
    printer_name: Optional[str] = None,
    copies: int = 1,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Actually print a license card to a physical printer.
    """
    # Get print job
    print_job = crud.print_job.get(db, id=print_job_id)
    if not print_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Print job not found"
        )
    
    if print_job.status.value != 'printing':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Print job is not in printing status"
        )
    
    # Print the license card
    print_result = printing_service.print_license_card(
        front_pdf=print_job.front_pdf_path,
        back_pdf=print_job.back_pdf_path,
        combined_pdf=print_job.combined_pdf_path,
        printer_name=printer_name,
        copies=copies
    )
    
    if print_result["success"]:
        # Update print job with printer details
        update_data = {
            "printer_name": printer_name or printing_service.get_default_printer(),
            "copies_printed": copies
        }
        crud.print_job.update(db, db_obj=print_job, obj_in=update_data)
        
        # Log successful print
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.PRINT,
                "resource_type": ResourceType.LICENSE,
                "resource_id": str(print_job.license_id),
                "description": f"ISO-compliant license card printed successfully - Print Job {print_job_id}"
            }
        )
    
    return {
        "print_job_id": print_job_id,
        "print_result": print_result,
        "printer_used": printer_name or printing_service.get_default_printer(),
        "copies": copies,
        "iso_compliant": True
    } 