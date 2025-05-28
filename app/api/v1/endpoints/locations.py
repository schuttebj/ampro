from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.user import User, UserRole
from app.schemas.location import Location, LocationCreate, LocationUpdate, LocationSummary
from app.models.audit import ActionType, ResourceType

router = APIRouter()


def check_location_permissions(current_user: User) -> None:
    """Check if user can manage locations"""
    if not current_user.can_manage_locations:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to manage locations"
        )


@router.get("/", response_model=List[Location])
def read_locations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve locations.
    """
    locations = crud.location.get_multi(db, skip=skip, limit=limit)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LOCATION,
            "description": f"User {current_user.username} retrieved list of locations"
        }
    )
    
    return locations


@router.get("/active", response_model=List[LocationSummary])
def read_active_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve active locations for dropdowns.
    """
    locations = crud.location.get_active_locations(db)
    return locations


@router.get("/accepting-applications", response_model=List[LocationSummary])
def read_locations_accepting_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve locations that accept new applications.
    """
    locations = crud.location.get_locations_accepting_applications(db)
    return locations


@router.get("/accepting-collections", response_model=List[LocationSummary])
def read_locations_accepting_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve locations that accept license collections.
    """
    locations = crud.location.get_locations_accepting_collections(db)
    return locations


@router.post("/", response_model=Location)
def create_location(
    *,
    db: Session = Depends(get_db),
    location_in: LocationCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new location.
    """
    check_location_permissions(current_user)
    
    # Check if location code already exists
    if location_in.code:
        existing_location = crud.location.get_by_code(db, code=location_in.code)
        if existing_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A location with this code already exists",
            )
    
    # Create location
    location = crud.location.create_with_code(db, obj_in=location_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.LOCATION,
            "resource_id": str(location.id),
            "description": f"User {current_user.username} created location {location.name} ({location.code})"
        }
    )
    
    return location


@router.get("/{location_id}", response_model=Location)
def read_location(
    *,
    db: Session = Depends(get_db),
    location_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get location by ID.
    """
    location = crud.location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.LOCATION,
            "resource_id": str(location.id),
            "description": f"User {current_user.username} viewed location {location.name}"
        }
    )
    
    return location


@router.put("/{location_id}", response_model=Location)
def update_location(
    *,
    db: Session = Depends(get_db),
    location_id: int,
    location_in: LocationUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a location.
    """
    check_location_permissions(current_user)
    
    location = crud.location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    # Check if updating code and it already exists
    if location_in.code and location_in.code != location.code:
        existing_location = crud.location.get_by_code(db, code=location_in.code)
        if existing_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A location with this code already exists",
            )
    
    # Update location
    location = crud.location.update(db, db_obj=location, obj_in=location_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.LOCATION,
            "resource_id": str(location.id),
            "description": f"User {current_user.username} updated location {location.name}"
        }
    )
    
    return location


@router.delete("/{location_id}", response_model=Location)
def delete_location(
    *,
    db: Session = Depends(get_db),
    location_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a location (soft delete).
    """
    check_location_permissions(current_user)
    
    location = crud.location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    # Check if location has active users or applications
    if location.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete location that has assigned users"
        )
    
    # Soft delete location
    location = crud.location.soft_delete(db, id=location_id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.DELETE,
            "resource_type": ResourceType.LOCATION,
            "resource_id": str(location.id),
            "description": f"User {current_user.username} deleted location {location.name}"
        }
    )
    
    return location


@router.put("/{location_id}/status", response_model=Location)
def update_location_status(
    *,
    db: Session = Depends(get_db),
    location_id: int,
    is_active: bool,
    accepts_applications: bool = None,
    accepts_collections: bool = None,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update location status.
    """
    check_location_permissions(current_user)
    
    location = crud.location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    # Update status
    location = crud.location.update_status(
        db,
        db_obj=location,
        is_active=is_active,
        accepts_applications=accepts_applications,
        accepts_collections=accepts_collections
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.LOCATION,
            "resource_id": str(location.id),
            "description": f"User {current_user.username} updated status for location {location.name}"
        }
    )
    
    return location 