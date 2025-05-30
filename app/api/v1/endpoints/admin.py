from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.user import UserRole
from app.models.printer import PrinterStatus, PrinterType

router = APIRouter()


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/users", response_model=List[schemas.User])
def get_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    location_id: Optional[int] = None,
    search: Optional[str] = None,
    can_print: Optional[bool] = None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users with filtering options.
    """
    if search or role or location_id or can_print is not None:
        users = crud.user.search_users(
            db, 
            role=role, 
            location_id=location_id, 
            search_term=search,
            can_print=can_print
        )
        return users[skip : skip + limit]
    else:
        users = crud.user.get_multi(db, skip=skip, limit=limit)
        return users


@router.post("/users", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user


@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.get("/users/{user_id}", response_model=schemas.User)
def get_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}")
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a user.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(status_code=400, detail="Users cannot delete themselves")
    user = crud.user.remove(db, id=user_id)
    return {"message": "User deleted successfully"}


# ============================================================================
# PRINTER USER MANAGEMENT
# ============================================================================

@router.get("/users/printers", response_model=List[schemas.User])
def get_printer_users(
    db: Session = Depends(deps.get_db),
    location_id: Optional[int] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all users with PRINTER role, optionally filtered by location.
    """
    if location_id:
        users = crud.user.get_printer_users_for_location(db, location_id=location_id)
    else:
        users = crud.user.get_printer_users(db)
    return users


# ============================================================================
# USER-LOCATION MANAGEMENT
# ============================================================================

@router.post("/users/{user_id}/locations/{location_id}")
def assign_user_to_location(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    location_id: int,
    is_primary: bool = False,
    can_print: bool = False,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Assign a user to a location.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    location = crud.location.get(db, id=location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    assignment = crud.user_location.assign_user_to_location(
        db, 
        user_id=user_id, 
        location_id=location_id,
        is_primary=is_primary,
        can_print=can_print
    )
    return {"message": "User assigned to location successfully", "assignment": assignment}


@router.delete("/users/{user_id}/locations/{location_id}")
def remove_user_from_location(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    location_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Remove a user from a location.
    """
    success = crud.user_location.remove_user_from_location(
        db, user_id=user_id, location_id=location_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="User-location assignment not found")
    return {"message": "User removed from location successfully"}


@router.put("/users/{user_id}/locations/{location_id}/primary")
def set_primary_location(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    location_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Set a location as primary for a user.
    """
    assignment = crud.user_location.set_primary_location(
        db, user_id=user_id, location_id=location_id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="User-location assignment not found")
    return {"message": "Primary location set successfully", "assignment": assignment}


@router.put("/users/{user_id}/locations/{location_id}/print-permission")
def update_print_permission(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    location_id: int,
    can_print: bool,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update print permission for user at location.
    """
    assignment = crud.user_location.update_print_permission(
        db, user_id=user_id, location_id=location_id, can_print=can_print
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="User-location assignment not found")
    return {"message": "Print permission updated successfully", "assignment": assignment}


@router.get("/users/{user_id}/locations", response_model=List[schemas.UserLocation])
def get_user_locations(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all locations for a specific user.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    locations = crud.user_location.get_user_locations(db, user_id=user_id)
    return locations


@router.get("/locations/{location_id}/users", response_model=List[schemas.UserLocation])
def get_location_users(
    location_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all users at a specific location.
    """
    location = crud.location.get(db, id=location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    users = crud.user_location.get_location_users(db, location_id=location_id)
    return users


# ============================================================================
# PRINTER MANAGEMENT
# ============================================================================

@router.get("/printers", response_model=List[schemas.Printer])
def get_printers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    location_id: Optional[int] = None,
    status: Optional[PrinterStatus] = None,
    printer_type: Optional[PrinterType] = None,
    search: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve printers with filtering options.
    """
    if location_id or status or printer_type or search:
        printers = crud.printer.search_printers(
            db,
            location_id=location_id,
            status=status,
            printer_type=printer_type,
            search_term=search
        )
        return printers[skip : skip + limit]
    else:
        printers = crud.printer.get_multi(db, skip=skip, limit=limit)
        return printers


@router.post("/printers", response_model=schemas.Printer)
def create_printer(
    *,
    db: Session = Depends(deps.get_db),
    printer_in: schemas.PrinterCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new printer.
    """
    printer = crud.printer.get_by_code(db, code=printer_in.code)
    if printer:
        raise HTTPException(
            status_code=400,
            detail="The printer with this code already exists in the system.",
        )
    printer = crud.printer.create(db, obj_in=printer_in)
    return printer


@router.put("/printers/{printer_id}", response_model=schemas.Printer)
def update_printer(
    *,
    db: Session = Depends(deps.get_db),
    printer_id: int,
    printer_in: schemas.PrinterUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a printer.
    """
    printer = crud.printer.get(db, id=printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    printer = crud.printer.update(db, db_obj=printer, obj_in=printer_in)
    return printer


@router.get("/printers/{printer_id}", response_model=schemas.Printer)
def get_printer_by_id(
    printer_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific printer by id.
    """
    printer = crud.printer.get(db, id=printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return printer


@router.delete("/printers/{printer_id}")
def delete_printer(
    *,
    db: Session = Depends(deps.get_db),
    printer_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a printer.
    """
    printer = crud.printer.get(db, id=printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    printer = crud.printer.remove(db, id=printer_id)
    return {"message": "Printer deleted successfully"}


@router.put("/printers/{printer_id}/status")
def update_printer_status(
    *,
    db: Session = Depends(deps.get_db),
    printer_id: int,
    status: PrinterStatus,
    notes: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update printer status.
    """
    printer = crud.printer.update_status(
        db, printer_id=printer_id, status=status, notes=notes
    )
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return {"message": "Printer status updated successfully", "printer": printer}


@router.put("/printers/{printer_id}/location/{location_id}")
def assign_printer_to_location(
    *,
    db: Session = Depends(deps.get_db),
    printer_id: int,
    location_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Assign printer to a location.
    """
    location = crud.location.get(db, id=location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    printer = crud.printer.assign_to_location(
        db, printer_id=printer_id, location_id=location_id
    )
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return {"message": "Printer assigned to location successfully", "printer": printer} 