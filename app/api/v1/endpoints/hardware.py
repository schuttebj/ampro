from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.hardware import HardwareType, HardwareStatus
from app.models.audit import ActionType, ResourceType
from app.schemas.hardware import (
    Hardware, HardwareCreate, HardwareUpdate, HardwareWithLocation,
    HardwareStatusUpdate, HardwareStatistics
)

router = APIRouter()


@router.get("/", response_model=List[HardwareWithLocation])
def get_hardware_list(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    location_id: Optional[int] = Query(None, description="Filter by location"),
    hardware_type: Optional[HardwareType] = Query(None, description="Filter by hardware type"),
    status: Optional[HardwareStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name, code, or model"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get hardware list with optional filters.
    """
    if search:
        hardware_list = crud.hardware.search_hardware(
            db,
            search_term=search,
            location_id=location_id,
            hardware_type=hardware_type,
            status=status,
            skip=skip,
            limit=limit
        )
    elif location_id:
        hardware_list = crud.hardware.get_by_location(
            db,
            location_id=location_id,
            hardware_type=hardware_type,
            status=status,
            skip=skip,
            limit=limit
        )
    elif hardware_type:
        hardware_list = crud.hardware.get_by_type(
            db,
            hardware_type=hardware_type,
            status=status,
            skip=skip,
            limit=limit
        )
    else:
        hardware_list = crud.hardware.get_multi(db, skip=skip, limit=limit)
    
    # Enrich with location information
    enriched_hardware = []
    for hardware in hardware_list:
        hardware_dict = hardware.__dict__.copy()
        if hardware.location:
            hardware_dict['location_name'] = hardware.location.name
            hardware_dict['location_code'] = hardware.location.code
        enriched_hardware.append(hardware_dict)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} retrieved hardware list"
        }
    )
    
    return enriched_hardware


@router.post("/", response_model=Hardware)
def create_hardware(
    *,
    db: Session = Depends(get_db),
    hardware_in: HardwareCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new hardware device.
    """
    # Check if hardware with this code exists
    existing_hardware = crud.hardware.get_by_code(db, code=hardware_in.code)
    if existing_hardware:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hardware with this code already exists",
        )
    
    # Verify location exists if provided
    if hardware_in.location_id:
        location = crud.location.get(db, id=hardware_in.location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location not found",
            )
    
    # Create hardware
    hardware = crud.hardware.create(db, obj_in=hardware_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.SYSTEM,
            "resource_id": str(hardware.id),
            "description": f"User {current_user.username} created hardware device {hardware.name} ({hardware.code})"
        }
    )
    
    return hardware


@router.get("/{hardware_id}", response_model=Hardware)
def get_hardware(
    *,
    db: Session = Depends(get_db),
    hardware_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get hardware by ID.
    """
    hardware = crud.hardware.get(db, id=hardware_id)
    if not hardware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found",
        )
    
    return hardware


@router.put("/{hardware_id}", response_model=Hardware)
def update_hardware(
    *,
    db: Session = Depends(get_db),
    hardware_id: int,
    hardware_in: HardwareUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update hardware device.
    """
    hardware = crud.hardware.get(db, id=hardware_id)
    if not hardware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found",
        )
    
    # Verify location exists if being updated
    if hardware_in.location_id:
        location = crud.location.get(db, id=hardware_in.location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location not found",
            )
    
    hardware = crud.hardware.update(db, db_obj=hardware, obj_in=hardware_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.SYSTEM,
            "resource_id": str(hardware.id),
            "description": f"User {current_user.username} updated hardware device {hardware.name} ({hardware.code})"
        }
    )
    
    return hardware


@router.post("/{hardware_id}/status", response_model=Hardware)
def update_hardware_status(
    *,
    db: Session = Depends(get_db),
    hardware_id: int,
    status_update: HardwareStatusUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update hardware status.
    """
    hardware = crud.hardware.update_status(
        db,
        hardware_id=hardware_id,
        status=status_update.status,
        notes=status_update.notes
    )
    
    if not hardware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found",
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.SYSTEM,
            "resource_id": str(hardware.id),
            "description": f"User {current_user.username} changed hardware {hardware.name} status to {status_update.status.value}"
        }
    )
    
    return hardware


@router.delete("/{hardware_id}", response_model=Hardware)
def delete_hardware(
    *,
    db: Session = Depends(get_db),
    hardware_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete hardware device (soft delete).
    """
    hardware = crud.hardware.get(db, id=hardware_id)
    if not hardware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found",
        )
    
    hardware = crud.hardware.remove(db, id=hardware_id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.DELETE,
            "resource_type": ResourceType.SYSTEM,
            "resource_id": str(hardware.id),
            "description": f"User {current_user.username} deleted hardware device {hardware.name} ({hardware.code})"
        }
    )
    
    return hardware


@router.get("/webcams/available", response_model=List[Hardware])
def get_available_webcams(
    *,
    db: Session = Depends(get_db),
    location_id: Optional[int] = Query(None, description="Filter by location"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get available webcams for photo capture from database.
    """
    webcams = crud.hardware.get_available_webcams(
        db,
        location_id=location_id or current_user.location_id
    )
    
    return webcams


@router.get("/debug")
def debug_hardware_data(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Debug endpoint to check what hardware is in the database.
    """
    try:
        # Get all hardware
        all_hardware = crud.hardware.get_multi(db, limit=100)
        
        # Get webcam hardware specifically
        webcam_hardware = crud.hardware.get_multi(
            db,
            filters={"hardware_type": HardwareType.WEBCAM},
            limit=100
        )
        
        return {
            "total_hardware_count": len(all_hardware),
            "webcam_count": len(webcam_hardware),
            "all_hardware": [
                {
                    "id": hw.id,
                    "name": hw.name,
                    "code": hw.code,
                    "hardware_type": hw.hardware_type,
                    "status": hw.status,
                    "device_id": hw.device_id
                }
                for hw in all_hardware
            ],
            "webcam_hardware": [
                {
                    "id": hw.id,
                    "name": hw.name,
                    "code": hw.code,
                    "hardware_type": hw.hardware_type,
                    "status": hw.status,
                    "device_id": hw.device_id
                }
                for hw in webcam_hardware
            ]
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "total_hardware_count": 0,
            "webcam_count": 0,
            "all_hardware": [],
            "webcam_hardware": []
        }


@router.get("/statistics", response_model=HardwareStatistics)
def get_hardware_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get hardware statistics.
    """
    stats = crud.hardware.get_statistics(db)
    
    # Add location names to location statistics
    if stats.get("by_location"):
        location_stats = {}
        for location_id, count in stats["by_location"].items():
            location = crud.location.get(db, id=location_id)
            location_name = location.name if location else f"Location {location_id}"
            location_stats[location_name] = count
        stats["by_location"] = location_stats
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} viewed hardware statistics"
        }
    )
    
    return HardwareStatistics(
        total_hardware=stats["total_hardware"],
        active_hardware=stats["active_hardware"],
        offline_hardware=stats["offline_hardware"],
        maintenance_hardware=stats["maintenance_hardware"],
        error_hardware=stats["error_hardware"],
        by_type=stats["by_type"],
        by_location=stats["by_location"],
        recent_usage=[]  # TODO: Implement usage log retrieval
    ) 