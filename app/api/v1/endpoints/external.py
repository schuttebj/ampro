from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType
from app.models.user import User
from app.models.citizen import Gender, MaritalStatus
from app.services.external_db import (
    ExternalCitizenDB, 
    ExternalDriverDB,
    ExternalInfringementDB,
    consolidate_citizen_data
)
from app.schemas.citizen import CitizenCreate

router = APIRouter()


@router.get("/citizen/{id_number}", response_model=Dict[str, Any])
def query_external_citizen_db(
    id_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Query the external citizen database by ID number.
    This simulates connecting to a government identity database.
    """
    # Validate ID number format
    if not id_number or len(id_number) != 13 or not id_number.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID number format. South African ID numbers must be 13 digits."
        )
    
    # Query external database
    citizen_data = ExternalCitizenDB.search_by_id_number(id_number)
    
    # Log the query
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} queried external citizen database for ID {id_number}"
        }
    )
    
    if not citizen_data:
        return {"success": False, "message": "No record found for the provided ID number"}
    
    return {"success": True, "data": citizen_data}


@router.get("/driver/{id_number}", response_model=Dict[str, Any])
def query_external_driver_db(
    id_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Query the external driver database by ID number.
    This simulates connecting to a driver licensing database.
    """
    # Validate ID number format
    if not id_number or len(id_number) != 13 or not id_number.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID number format. South African ID numbers must be 13 digits."
        )
    
    # Query external database
    driver_data = ExternalDriverDB.search_by_id_number(id_number)
    
    # Log the query
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} queried external driver database for ID {id_number}"
        }
    )
    
    if not driver_data:
        return {"success": False, "message": "No driver record found for the provided ID number"}
    
    return {"success": True, "data": driver_data}


@router.get("/infringement/{id_number}", response_model=Dict[str, Any])
def query_external_infringement_db(
    id_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Query the external infringement database by ID number.
    This simulates connecting to a traffic infringement database.
    """
    # Validate ID number format
    if not id_number or len(id_number) != 13 or not id_number.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID number format. South African ID numbers must be 13 digits."
        )
    
    # Query external database
    infringement_data = ExternalInfringementDB.search_by_id_number(id_number)
    
    # Log the query
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} queried external infringement database for ID {id_number}"
        }
    )
    
    if not infringement_data:
        return {"success": False, "message": "No infringement record found for the provided ID number"}
    
    return {"success": True, "data": infringement_data}


@router.get("/consolidated/{id_number}", response_model=Dict[str, Any])
def query_consolidated_data(
    id_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Query all external databases and consolidate the data.
    This simulates connecting to multiple government databases and merging the data.
    """
    # Validate ID number format
    if not id_number or len(id_number) != 13 or not id_number.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID number format. South African ID numbers must be 13 digits."
        )
    
    # Query external databases and consolidate data
    result = consolidate_citizen_data(id_number)
    
    # Log the query
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} queried consolidated external databases for ID {id_number}"
        }
    )
    
    if not result["success"]:
        return {"success": False, "message": "No record found for the provided ID number"}
    
    return result


@router.post("/import-citizen/{id_number}", response_model=Dict[str, Any])
def import_citizen_data(
    id_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Import citizen data from external databases into our system.
    """
    # Validate ID number format
    if not id_number or len(id_number) != 13 or not id_number.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID number format. South African ID numbers must be 13 digits."
        )
    
    # Check if citizen already exists
    existing_citizen = crud.citizen.get_by_id_number(db, id_number=id_number)
    if existing_citizen:
        return {
            "success": False, 
            "message": "Citizen already exists in the system",
            "citizen_id": existing_citizen.id
        }
    
    # Get consolidated data
    result = consolidate_citizen_data(id_number)
    
    if not result["success"]:
        return {"success": False, "message": "No record found in external databases"}
    
    # Process the data to create a citizen
    citizen_data = result["data"]
    
    # Map gender string to enum
    gender_map = {"male": Gender.MALE, "female": Gender.FEMALE}
    gender = gender_map.get(citizen_data.get("gender", "").lower(), None)
    
    # Map marital status string to enum
    marital_map = {
        "single": MaritalStatus.SINGLE,
        "married": MaritalStatus.MARRIED,
        "divorced": MaritalStatus.DIVORCED,
        "widowed": MaritalStatus.WIDOWED
    }
    marital_status = marital_map.get(citizen_data.get("marital_status", "").lower(), None)
    
    # Create citizen object
    citizen_create = CitizenCreate(
        id_number=id_number,
        first_name=citizen_data.get("first_name", ""),
        last_name=citizen_data.get("last_name", ""),
        middle_name=citizen_data.get("middle_name"),
        date_of_birth=citizen_data.get("date_of_birth"),
        gender=gender,
        marital_status=marital_status,
        phone_number=citizen_data.get("phone_number"),
        email=citizen_data.get("email"),
        address_line1=citizen_data.get("address_line1"),
        address_line2=citizen_data.get("address_line2"),
        city=citizen_data.get("city"),
        state_province=citizen_data.get("state_province"),
        postal_code=citizen_data.get("postal_code"),
        country=citizen_data.get("country"),
        birth_place=citizen_data.get("birth_place"),
        nationality=citizen_data.get("nationality"),
    )
    
    # Create citizen in database
    citizen = crud.citizen.create(db, obj_in=citizen_create)
    
    # Log the action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.CITIZEN,
            "resource_id": str(citizen.id),
            "description": f"User {current_user.username} imported citizen data from external databases for ID {id_number}"
        }
    )
    
    return {
        "success": True,
        "message": "Citizen data imported successfully",
        "citizen_id": citizen.id,
        "sources": result["sources"]
    } 