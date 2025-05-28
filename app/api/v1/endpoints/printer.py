from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_printer_user
from app.models.user import User
from app.models.license import PrintJobStatus
from app.models.audit import ActionType, ResourceType
from app.schemas.print_job import (
    PrintJob, PrintJobStart, PrintJobComplete, PrintQueue, PrintJobStatistics
)
from app.services.printing_service import printing_service

router = APIRouter()


@router.get("/dashboard", response_model=Dict[str, Any])
def get_printer_dashboard(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_printer_user),
) -> Any:
    """
    Get printer dashboard data for printer operators.
    """
    # Get print jobs assigned to current user
    assigned_jobs = crud.print_job.get_by_assigned_user(db, user_id=current_user.id)
    
    # Get print queue statistics
    queue_stats = crud.print_job.get_queue_statistics(db)
    
    # Get user's print statistics
    user_stats = crud.print_job.get_user_statistics(db, user_id=current_user.id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"Printer {current_user.username} accessed dashboard"
        }
    )
    
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "role": current_user.role.value
        },
        "assigned_jobs": assigned_jobs,
        "queue_statistics": queue_stats,
        "user_statistics": user_stats,
        "timestamp": datetime.utcnow()
    }


@router.get("/queue", response_model=PrintQueue)
def get_printer_queue(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_printer_user),
) -> Any:
    """
    Get print queue for printer operators.
    """
    # Get print jobs that are queued or assigned to current user
    print_jobs = crud.print_job.get_printer_queue(
        db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    
    total_count = crud.print_job.count_printer_queue(db, user_id=current_user.id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.APPLICATION,
            "description": f"Printer {current_user.username} viewed print queue"
        }
    )
    
    return {
        "print_jobs": print_jobs,
        "total_count": total_count,
        "skip": skip,
        "limit": limit
    }


@router.get("/jobs/assigned", response_model=List[PrintJob])
def get_assigned_jobs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_printer_user),
) -> Any:
    """
    Get print jobs assigned to current printer operator.
    """
    jobs = crud.print_job.get_by_assigned_user(db, user_id=current_user.id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.APPLICATION,
            "description": f"Printer {current_user.username} viewed assigned jobs"
        }
    )
    
    return jobs


@router.post("/jobs/{print_job_id}/start", response_model=PrintJob)
def start_print_job(
    *,
    db: Session = Depends(get_db),
    print_job_id: int,
    start_data: PrintJobStart,
    current_user: User = Depends(get_current_printer_user),
) -> Any:
    """
    Start a print job (printer operators only).
    """
    # Get print job
    print_job = crud.print_job.get(db, id=print_job_id)
    if not print_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Print job not found"
        )
    
    # Check if job is assigned to current user
    if print_job.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Print job not assigned to you"
        )
    
    # Check if job can be started
    if print_job.status != PrintJobStatus.ASSIGNED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Print job cannot be started (not in assigned status)"
        )
    
    # Start print job
    print_job = crud.print_job.start_printing(
        db, 
        print_job_id=print_job_id, 
        printer_name=start_data.printer_name
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.PRINT,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(print_job.application_id),
            "description": f"Print job {print_job_id} started by printer {current_user.username}"
        }
    )
    
    return print_job


@router.post("/jobs/{print_job_id}/complete", response_model=Dict[str, Any])
def complete_print_job(
    *,
    db: Session = Depends(get_db),
    print_job_id: int,
    complete_data: PrintJobComplete,
    current_user: User = Depends(get_current_printer_user),
) -> Any:
    """
    Complete a print job (printer operators only).
    """
    # Get print job
    print_job = crud.print_job.get(db, id=print_job_id)
    if not print_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Print job not found"
        )
    
    # Check if job is assigned to current user
    if print_job.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Print job not assigned to you"
        )
    
    # Check if job can be completed
    if print_job.status != PrintJobStatus.PRINTING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Print job cannot be completed (not in printing status)"
        )
    
    # Complete print job
    result = crud.print_job.complete_printing(
        db, 
        print_job_id=print_job_id, 
        quality_check_passed=complete_data.quality_check_passed,
        notes=complete_data.notes
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(print_job.application_id),
            "description": f"Print job {print_job_id} completed by printer {current_user.username}"
        }
    )
    
    return {
        "message": "Print job completed successfully",
        "print_job_id": print_job_id,
        "application_id": print_job.application_id,
        "quality_check_passed": complete_data.quality_check_passed,
        "completed_at": result.completed_at
    }


@router.get("/jobs/{print_job_id}/application", response_model=Dict[str, Any])
def get_application_for_print_job(
    *,
    db: Session = Depends(get_db),
    print_job_id: int,
    current_user: User = Depends(get_current_printer_user),
) -> Any:
    """
    Get application details for a print job (printer operators only).
    """
    # Get print job
    print_job = crud.print_job.get(db, id=print_job_id)
    if not print_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Print job not found"
        )
    
    # Check if job is assigned to current user
    if print_job.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Print job not assigned to you"
        )
    
    # Get application and citizen data
    application = crud.license_application.get(db, id=print_job.application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    citizen = crud.citizen.get(db, id=application.citizen_id)
    license = crud.license.get(db, id=print_job.license_id) if print_job.license_id else None
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.APPLICATION,
            "resource_id": str(application.id),
            "description": f"Printer {current_user.username} viewed application {application.id} for printing"
        }
    )
    
    return {
        "print_job": print_job,
        "application": application,
        "citizen": citizen,
        "license": license,
        "print_files": {
            "front_pdf": print_job.front_pdf_path,
            "back_pdf": print_job.back_pdf_path,
            "combined_pdf": print_job.combined_pdf_path
        }
    }


@router.get("/statistics", response_model=PrintJobStatistics)
def get_printer_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_printer_user),
) -> Any:
    """
    Get print job statistics for current printer operator.
    """
    stats = crud.print_job.get_user_statistics(db, user_id=current_user.id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"Printer {current_user.username} viewed statistics"
        }
    )
    
    return stats


@router.get("/printers", response_model=List[Dict[str, str]])
def get_available_printers(
    *,
    current_user: User = Depends(get_current_printer_user),
) -> Any:
    """
    Get available printers for printer operators.
    """
    printers = printing_service.get_available_printers()
    
    return [
        {"name": printer, "status": "available"} 
        for printer in printers
    ] 