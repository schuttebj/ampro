from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType
from app.models.license import LicenseCategory, TransactionType, ApplicationType
from app.models.user import User
from app.schemas.license import (
    LicenseFee, 
    LicenseFeeCreate, 
    LicenseFeeUpdate
)

router = APIRouter()


@router.get("/", response_model=List[LicenseFee])
def read_license_fees(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    license_category: str = None,
    transaction_type: str = None,
    application_type: str = None,
    is_active: bool = None,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve license fees with optional filtering.
    """
    if is_active is True:
        fees = crud.license_fee.get_active_fees(db, skip=skip, limit=limit)
    elif license_category:
        try:
            category_enum = LicenseCategory(license_category)
            fees = crud.license_fee.get_fees_by_category(db, license_category=category_enum)
        except ValueError:
            fees = crud.license_fee.get_multi(db, skip=skip, limit=limit)
    else:
        fees = crud.license_fee.get_multi(db, skip=skip, limit=limit)
    
    # Apply additional filters
    if transaction_type:
        try:
            transaction_enum = TransactionType(transaction_type)
            fees = [f for f in fees if f.transaction_type == transaction_enum]
        except ValueError:
            pass
    
    if application_type:
        try:
            app_type_enum = ApplicationType(application_type)
            fees = [f for f in fees if f.application_type == app_type_enum]
        except ValueError:
            pass
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.FEE,
            "description": f"User {current_user.username} retrieved list of license fees"
        }
    )
    
    return fees


@router.post("/", response_model=LicenseFee)
def create_license_fee(
    *,
    db: Session = Depends(get_db),
    fee_in: LicenseFeeCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new license fee.
    """
    # Check if fee already exists for this combination
    existing_fee = crud.license_fee.get_by_category_and_type(
        db,
        license_category=fee_in.license_category,
        transaction_type=fee_in.transaction_type,
        application_type=fee_in.application_type
    )
    
    if existing_fee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fee already exists for {fee_in.license_category}-{fee_in.transaction_type}-{fee_in.application_type}",
        )
    
    # Create fee
    fee = crud.license_fee.create(db, obj_in=fee_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.FEE,
            "resource_id": str(fee.id),
            "description": f"User {current_user.username} created license fee for {fee.license_category}-{fee.transaction_type}-{fee.application_type}"
        }
    )
    
    return fee


@router.get("/calculate", response_model=Dict[str, Any])
def calculate_fee(
    db: Session = Depends(get_db),
    license_category: str = None,
    transaction_type: str = None,
    application_type: str = None,
    applicant_age: int = None,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Calculate fee for a specific license application.
    """
    if not all([license_category, transaction_type, application_type]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="license_category, transaction_type, and application_type are required",
        )
    
    try:
        category_enum = LicenseCategory(license_category)
        transaction_enum = TransactionType(transaction_type)
        app_type_enum = ApplicationType(application_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid enum value: {str(e)}",
        )
    
    # Calculate fee
    total_fee = crud.license_fee.calculate_fee_for_application(
        db,
        license_category=category_enum,
        transaction_type=transaction_enum,
        application_type=app_type_enum,
        applicant_age=applicant_age
    )
    
    if total_fee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fee configuration found for the specified criteria",
        )
    
    # Get the fee record for details
    fee_record = crud.license_fee.get_by_category_and_type(
        db,
        license_category=category_enum,
        transaction_type=transaction_enum,
        application_type=app_type_enum
    )
    
    result = {
        "license_category": license_category,
        "transaction_type": transaction_type,
        "application_type": application_type,
        "applicant_age": applicant_age,
        "total_fee_cents": total_fee,
        "total_fee_rands": total_fee / 100,
        "fee_breakdown": {
            "base_fee_cents": fee_record.base_fee,
            "processing_fee_cents": fee_record.processing_fee,
            "delivery_fee_cents": fee_record.delivery_fee,
            "base_fee_rands": fee_record.base_fee / 100,
            "processing_fee_rands": fee_record.processing_fee / 100,
            "delivery_fee_rands": fee_record.delivery_fee / 100,
        } if fee_record else None
    }
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.FEE,
            "description": f"User {current_user.username} calculated fee for {license_category}-{transaction_type}-{application_type}"
        }
    )
    
    return result


@router.get("/{fee_id}", response_model=LicenseFee)
def read_license_fee(
    *,
    db: Session = Depends(get_db),
    fee_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get license fee by ID.
    """
    fee = crud.license_fee.get(db, id=fee_id)
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License fee not found",
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.FEE,
            "resource_id": str(fee.id),
            "description": f"User {current_user.username} viewed license fee {fee.license_category}-{fee.transaction_type}"
        }
    )
    
    return fee


@router.put("/{fee_id}", response_model=LicenseFee)
def update_license_fee(
    *,
    db: Session = Depends(get_db),
    fee_id: int,
    fee_in: LicenseFeeUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a license fee.
    """
    fee = crud.license_fee.get(db, id=fee_id)
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License fee not found",
        )
    
    fee = crud.license_fee.update(db, db_obj=fee, obj_in=fee_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.FEE,
            "resource_id": str(fee.id),
            "description": f"User {current_user.username} updated license fee {fee.license_category}-{fee.transaction_type}"
        }
    )
    
    return fee


@router.delete("/{fee_id}", response_model=LicenseFee)
def delete_license_fee(
    *,
    db: Session = Depends(get_db),
    fee_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a license fee (mark as inactive).
    """
    fee = crud.license_fee.get(db, id=fee_id)
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License fee not found",
        )
    
    # Mark as inactive instead of deleting
    fee = crud.license_fee.update(db, db_obj=fee, obj_in={"is_active": False})
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.DELETE,
            "resource_type": ResourceType.FEE,
            "resource_id": str(fee.id),
            "description": f"User {current_user.username} deactivated license fee {fee.license_category}-{fee.transaction_type}"
        }
    )
    
    return fee


@router.get("/matrix/all", response_model=List[Dict[str, Any]])
def get_fee_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get fee matrix showing all combinations and their fees.
    """
    fees = crud.license_fee.get_active_fees(db)
    
    matrix = []
    for fee in fees:
        matrix.append({
            "id": fee.id,
            "license_category": fee.license_category,
            "transaction_type": fee.transaction_type,
            "application_type": fee.application_type,
            "base_fee_rands": fee.base_fee / 100,
            "processing_fee_rands": fee.processing_fee / 100,
            "delivery_fee_rands": fee.delivery_fee / 100,
            "total_fee_rands": fee.total_fee() / 100,
            "minimum_age": fee.minimum_age,
            "maximum_age": fee.maximum_age,
            "description": fee.description,
            "effective_date": fee.effective_date,
            "is_active": fee.is_active
        })
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.FEE,
            "description": f"User {current_user.username} viewed fee matrix"
        }
    )
    
    return matrix 