from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType
from app.models.user import User
from app.schemas.audit import Transaction, TransactionDetail

router = APIRouter()


@router.get("/", response_model=List[Transaction])
def read_transactions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve transactions.
    """
    transactions = crud.transaction.get_multi(db, skip=skip, limit=limit)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} retrieved transaction list"
        }
    )
    
    return transactions


@router.get("/{transaction_id}", response_model=TransactionDetail)
def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get transaction by ID.
    """
    transaction = crud.transaction.get(db, id=transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "resource_id": str(transaction.id),
            "description": f"User {current_user.username} viewed transaction {transaction.transaction_ref}"
        }
    )
    
    return transaction


@router.get("/ref/{transaction_ref}", response_model=TransactionDetail)
def read_transaction_by_ref(
    transaction_ref: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get transaction by reference.
    """
    transaction = crud.transaction.get_by_transaction_ref(db, transaction_ref=transaction_ref)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "resource_id": str(transaction.id),
            "description": f"User {current_user.username} viewed transaction {transaction.transaction_ref}"
        }
    )
    
    return transaction


@router.get("/citizen/{citizen_id}", response_model=List[Transaction])
def read_citizen_transactions(
    citizen_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all transactions for a citizen.
    """
    # Check if citizen exists
    citizen = crud.citizen.get(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found"
        )
    
    transactions = crud.transaction.get_by_citizen_id(db, citizen_id=citizen_id, skip=skip, limit=limit)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} viewed transactions for citizen {citizen.id_number}"
        }
    )
    
    return transactions


@router.get("/license/{license_id}", response_model=List[Transaction])
def read_license_transactions(
    license_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all transactions for a license.
    """
    # Check if license exists
    license = crud.license.get(db, id=license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    transactions = crud.transaction.get_multi_by_field(
        db, field_name="license_id", value=license_id, skip=skip, limit=limit
    )
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} viewed transactions for license {license.license_number}"
        }
    )
    
    return transactions 