from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType
from app.models.user import User
from app.schemas.citizen import Citizen, CitizenCreate, CitizenUpdate
from app.services.file_manager import file_manager

router = APIRouter()


@router.get("/", response_model=List[Citizen])
def read_citizens(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = Query(False, description="Include inactive citizens (admin only)"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve citizens. By default only returns active citizens.
    """
    if include_inactive and not (current_user.is_superuser or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view inactive citizens",
        )
    
    if include_inactive:
        citizens = crud.citizen.get_multi(db, skip=skip, limit=limit)
    else:
        citizens = crud.citizen.get_active_citizens(db, skip=skip, limit=limit)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.CITIZEN,
            "description": f"User {current_user.username} retrieved list of {'all' if include_inactive else 'active'} citizens"
        }
    )
    
    return citizens


@router.post("/", response_model=Citizen)
def create_citizen(
    *,
    db: Session = Depends(get_db),
    citizen_in: CitizenCreate,
    background_tasks: BackgroundTasks,
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
    
    # Handle photo processing if photo URL provided
    if hasattr(citizen_in, 'photo_url') and citizen_in.photo_url:
        try:
            # Download and process photo
            original_path, processed_path = file_manager.download_and_store_photo(
                citizen_in.photo_url, citizen.id
            )
            
            # Update citizen with photo paths
            crud.citizen.update_photo_paths(
                db,
                citizen_id=citizen.id,
                stored_photo_path=original_path,
                processed_photo_path=processed_path
            )
            
        except Exception as e:
            # Log the error but don't fail the creation
            crud.audit_log.create(
                db,
                obj_in={
                    "user_id": current_user.id,
                    "action_type": ActionType.CREATE,
                    "resource_type": ResourceType.CITIZEN,
                    "resource_id": str(citizen.id),
                    "description": f"Photo processing failed for new citizen {citizen.first_name} {citizen.last_name}: {str(e)}"
                }
            )
    
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
    include_inactive: bool = Query(False, description="Include inactive citizens (admin only)"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Search citizens by ID number or name. By default only searches active citizens.
    Uses more precise matching logic.
    """
    from app.models.citizen import Citizen as CitizenModel
    
    if include_inactive and not (current_user.is_superuser or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can search inactive citizens",
        )
    
    # Build base query
    query = db.query(CitizenModel)
    
    # Filter by active status if needed
    if not include_inactive:
        query = query.filter(CitizenModel.is_active == True)
    
    search_conditions = []
    
    # Search by ID number (exact match or prefix for South African ID format)
    if id_number:
        # For ID numbers, be more precise - exact match or starts with
        search_conditions.append(
            or_(
                CitizenModel.id_number == id_number,  # Exact match
                CitizenModel.id_number.ilike(f"{id_number}%")  # Starts with
            )
        )
    
    # Search by name - only if we have both first and last name, use AND logic
    name_conditions = []
    if first_name:
        name_conditions.append(CitizenModel.first_name.ilike(f"%{first_name}%"))
    
    if last_name:
        name_conditions.append(CitizenModel.last_name.ilike(f"%{last_name}%"))
    
    # If we have both first and last name, use AND (more precise)
    # If we have only one, use OR (less precise but acceptable for single terms)
    if len(name_conditions) >= 2:
        # Both first and last name provided - use AND for precision
        search_conditions.append(and_(*name_conditions))
    elif len(name_conditions) == 1:
        # Only one name field provided - add it directly
        search_conditions.extend(name_conditions)
    
    # Apply search conditions
    if search_conditions:
        # Use OR between ID search and name search, but AND within name search
        query = query.filter(or_(*search_conditions))
        
        try:
            results = query.offset(skip).limit(limit).all()
        except Exception as e:
            # Handle database errors gracefully
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during search: {str(e)}"
            )
    else:
        results = []
    
    # Log action
    search_terms = ", ".join(
        [f"{k}: {v}" for k, v in {"id_number": id_number, "first_name": first_name, "last_name": last_name}.items() if v]
    )
    
    try:
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.READ,
                "resource_type": ResourceType.CITIZEN,
                "description": f"User {current_user.username} searched {'all' if include_inactive else 'active'} citizens by {search_terms}, found {len(results)} results"
            }
        )
    except Exception as e:
        # Don't fail the search if audit logging fails
        pass
    
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
    background_tasks: BackgroundTasks,
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
    
    # Check if photo URL is being updated
    photo_url_changed = False
    new_photo_url = None
    
    if hasattr(citizen_in, 'photo_url') and citizen_in.photo_url is not None:
        if citizen_in.photo_url != citizen.photo_url:
            photo_url_changed = True
            new_photo_url = citizen_in.photo_url
    
    # Update citizen
    citizen = crud.citizen.update(db, db_obj=citizen, obj_in=citizen_in)
    
    # Handle photo processing if photo URL changed
    if photo_url_changed and new_photo_url:
        try:
            # Store old photo paths for cleanup
            old_stored_path = citizen.stored_photo_path
            old_processed_path = citizen.processed_photo_path
            
            # Download and process new photo
            original_path, processed_path = file_manager.download_and_store_photo(
                new_photo_url, citizen_id
            )
            
            # Update citizen with new photo paths
            crud.citizen.update_photo_paths(
                db,
                citizen_id=citizen_id,
                stored_photo_path=original_path,
                processed_photo_path=processed_path
            )
            
            # Only clean up old files after all database operations are successful
            if old_stored_path or old_processed_path:
                background_tasks.add_task(
                    file_manager.cleanup_old_files, 
                    citizen_id, 
                    exclude_paths=[original_path, processed_path]
                )
            
        except Exception as e:
            # Log the error but don't fail the update
            crud.audit_log.create(
                db,
                obj_in={
                    "user_id": current_user.id,
                    "action_type": ActionType.UPDATE,
                    "resource_type": ResourceType.CITIZEN,
                    "resource_id": str(citizen.id),
                    "description": f"Photo processing failed for citizen {citizen.first_name} {citizen.last_name}: {str(e)}"
                }
            )
    
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
    
    # Clean up citizen files before deletion
    file_manager.cleanup_citizen_files(citizen_id, keep_latest=False)
    
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


@router.post("/{citizen_id}/photo/update", response_model=Dict[str, Any])
def update_citizen_photo(
    *,
    db: Session = Depends(get_db),
    citizen_id: int,
    photo_url: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update citizen photo from uploaded file URL and process for ISO compliance.
    """
    citizen = crud.citizen.get(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    try:
        # Store old photo paths for cleanup
        old_stored_path = citizen.stored_photo_path
        old_processed_path = citizen.processed_photo_path
        
        # Update photo URL in database
        crud.citizen.update(db, db_obj=citizen, obj_in={"photo_url": photo_url})
        
        # Download and process new photo
        original_path, processed_path = file_manager.download_and_store_photo(
            photo_url, citizen_id
        )
        
        # Update citizen with new photo paths
        crud.citizen.update_photo_paths(
            db,
            citizen_id=citizen_id,
            stored_photo_path=original_path,
            processed_photo_path=processed_path
        )
        
        # Only clean up old files after all database operations are successful
        if old_stored_path or old_processed_path:
            background_tasks.add_task(
                file_manager.cleanup_old_files, 
                citizen_id, 
                exclude_paths=[original_path, processed_path]
            )
        
        # Log the photo update action
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.UPDATE,
                "resource_type": ResourceType.CITIZEN,
                "resource_id": str(citizen.id),
                "description": f"User {current_user.username} updated photo for citizen {citizen.first_name} {citizen.last_name}"
            }
        )
        
        return {
            "message": "Photo updated successfully",
            "citizen_id": citizen_id,
            "original_photo_path": original_path,
            "processed_photo_path": processed_path,
            "photo_url": photo_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating photo: {str(e)}"
        )


@router.delete("/{citizen_id}/photo", response_model=Dict[str, str])
def delete_citizen_photo(
    *,
    db: Session = Depends(get_db),
    citizen_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete citizen photo and clean up files.
    """
    citizen = crud.citizen.get(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    try:
        # Clear photo data in database
        crud.citizen.clear_photo_data(db, citizen_id=citizen_id)
        
        # Clean up all photo files in background
        background_tasks.add_task(file_manager.cleanup_citizen_files, citizen_id, keep_latest=False)
        
        # Log action
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.DELETE,
                "resource_type": ResourceType.CITIZEN,
                "resource_id": str(citizen.id),
                "description": f"User {current_user.username} deleted photo for citizen {citizen.first_name} {citizen.last_name}"
            }
        )
        
        return {
            "message": "Photo deleted successfully",
            "citizen_id": str(citizen_id)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting photo: {str(e)}"
        )


@router.get("/{citizen_id}/photo/status", response_model=Dict[str, Any])
def get_citizen_photo_status(
    *,
    db: Session = Depends(get_db),
    citizen_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get citizen photo processing status and file information.
    """
    citizen = crud.citizen.get(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found",
        )
    
    # Check file existence
    original_exists = False
    processed_exists = False
    
    if citizen.stored_photo_path:
        original_exists = file_manager.file_exists(citizen.stored_photo_path)
    
    if citizen.processed_photo_path:
        processed_exists = file_manager.file_exists(citizen.processed_photo_path)
    
    return {
        "citizen_id": citizen_id,
        "has_photo_url": bool(citizen.photo_url),
        "photo_url": citizen.photo_url,
        "stored_photo_path": citizen.stored_photo_path,
        "processed_photo_path": citizen.processed_photo_path,
        "original_file_exists": original_exists,
        "processed_file_exists": processed_exists,
        "photo_uploaded_at": citizen.photo_uploaded_at,
        "photo_processed_at": citizen.photo_processed_at,
        "needs_processing": bool(citizen.photo_url and not processed_exists)
    } 