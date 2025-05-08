from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType
from app.models.user import User
from app.schemas.citizen import Citizen, CitizenCreate, CitizenUpdate

router = APIRouter()


@router.get("/", response_model=List[Citizen])
def read_citizens(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve citizens.
    """
    citizens = crud.citizen.get_multi(db, skip=skip, limit=limit)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.CITIZEN,
            "description": f"User {current_user.username} retrieved list of citizens"
        }
    )
    
    return citizens


@router.post("/", response_model=Citizen)
def create_citizen(
    *,
    db: Session = Depends(get_db),
    citizen_in: CitizenCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new citizen.
    """
    # Check if citizen with this ID number exists
    citizen = crud.citizen.get_by_id_number(db, id_number=citizen_in.id_number)
    if citizen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A citizen with this ID number already exists",
        )
    
    # Create citizen
    citizen = crud.citizen.create(db, obj_in=citizen_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.CITIZEN,
            "resource_id": str(citizen.id),
            "description": f"User {current_user.username} created citizen record for {citizen.first_name} {citizen.last_name}"
        }
    )
    
    return citizen


@router.get("/search", response_model=List[Citizen])
def search_citizens(
    *,
    db: Session = Depends(get_db),
    id_number: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Search citizens by ID number or name.
    """
    # Search by ID number
    if id_number:
        citizen = crud.citizen.get_by_id_number(db, id_number=id_number)
        results = [citizen] if citizen else []
    # Search by name
    elif first_name or last_name:
        results = crud.citizen.search_by_name(
            db, first_name=first_name, last_name=last_name, skip=skip, limit=limit
        )
    else:
        results = []
    
    # Log action
    search_terms = ", ".join(
        [f"{k}: {v}" for k, v in {"id_number": id_number, "first_name": first_name, "last_name": last_name}.items() if v]
    )
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.CITIZEN,
            "description": f"User {current_user.username} searched citizens by {search_terms}"
        }
    )
    
    return results


@router.get("/{citizen_id}", response_model=Citizen)
def read_citizen(
    *,
    db: Session = Depends(get_db),
    citizen_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get citizen by ID.
    """
    citizen = crud.citizen.get(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.CITIZEN,
            "resource_id": str(citizen.id),
            "description": f"User {current_user.username} viewed citizen {citizen.first_name} {citizen.last_name}"
        }
    )
    
    return citizen


@router.put("/{citizen_id}", response_model=Citizen)
def update_citizen(
    *,
    db: Session = Depends(get_db),
    citizen_id: int,
    citizen_in: CitizenUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a citizen.
    """
    citizen = crud.citizen.get(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Log old values
    old_values = jsonable_encoder(citizen)
    
    # Update citizen
    citizen = crud.citizen.update(db, db_obj=citizen, obj_in=citizen_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.CITIZEN,
            "resource_id": str(citizen.id),
            "description": f"User {current_user.username} updated citizen {citizen.first_name} {citizen.last_name}",
            "old_values": old_values,
            "new_values": jsonable_encoder(citizen)
        }
    )
    
    return citizen


@router.get("/{citizen_id}/licenses", response_model=Dict)
def read_citizen_licenses(
    *,
    db: Session = Depends(get_db),
    citizen_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all licenses for a citizen.
    """
    # Get citizen with licenses
    citizen = crud.citizen.get_with_licenses(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.CITIZEN,
            "resource_id": str(citizen.id),
            "description": f"User {current_user.username} viewed licenses for citizen {citizen.first_name} {citizen.last_name}"
        }
    )
    
    # Convert to dict to avoid pydantic validation issues
    return {
        "citizen": jsonable_encoder(citizen),
        "licenses": jsonable_encoder(citizen.licenses)
    }


@router.delete("/{citizen_id}", response_model=Citizen)
def delete_citizen(
    *,
    db: Session = Depends(get_db),
    citizen_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a citizen (soft delete).
    """
    citizen = crud.citizen.get(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Soft delete citizen
    citizen = crud.citizen.soft_delete(db, id=citizen_id)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.DELETE,
            "resource_type": ResourceType.CITIZEN,
            "resource_id": str(citizen.id),
            "description": f"User {current_user.username} deleted citizen {citizen.first_name} {citizen.last_name}"
        }
    )
    
    return citizen 