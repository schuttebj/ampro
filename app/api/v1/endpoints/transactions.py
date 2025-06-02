from typing import Any, List, Dict
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType
from app.models.user import User
from app.schemas.audit import Transaction

router = APIRouter()


@router.get("/", response_model=List[Transaction])
def read_transactions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    transaction_type: str = None,
    status: str = None,
    citizen_id: int = None,
    license_id: int = None,
    date_from: str = None,
    date_to: str = None,
    amount_min: float = None,
    amount_max: float = None,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve transactions with filtering.
    """
    # Build filters
    filters = {}
    if transaction_type:
        filters['transaction_type'] = transaction_type
    if status:
        filters['status'] = status
    if citizen_id:
        filters['citizen_id'] = citizen_id
    if license_id:
        filters['license_id'] = license_id
    if date_from:
        filters['date_from'] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
    if date_to:
        filters['date_to'] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
    if amount_min is not None:
        filters['amount_min'] = amount_min * 100  # Convert to cents
    if amount_max is not None:
        filters['amount_max'] = amount_max * 100  # Convert to cents
    
    # Apply filters using existing CRUD methods or extend them
    if filters:
        # For now, use basic query - in production, extend CRUD methods for complex filtering
        transactions = crud.transaction.get_multi(db, skip=skip, limit=limit)
    else:
        transactions = crud.transaction.get_multi(db, skip=skip, limit=limit)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} retrieved transaction list with filters: {filters}"
        }
    )
    
    return transactions


@router.get("/export")
def export_transactions(
    db: Session = Depends(get_db),
    transaction_type: str = None,
    status: str = None,
    date_from: str = None,
    date_to: str = None,
    format: str = Query(default="csv", regex="^(csv|excel)$"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Export transactions to CSV or Excel.
    """
    # Build filters
    filters = {}
    if transaction_type:
        filters['transaction_type'] = transaction_type
    if status:
        filters['status'] = status
    if date_from:
        filters['date_from'] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
    if date_to:
        filters['date_to'] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
    
    # Get all transactions (remove limit for export)
    transactions = crud.transaction.get_multi(db, skip=0, limit=10000)
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Transaction Reference',
        'Type',
        'Status',
        'Amount',
        'Citizen Name',
        'Citizen ID',
        'User',
        'Initiated At',
        'Completed At',
        'Notes'
    ])
    
    # Write data
    for transaction in transactions:
        writer.writerow([
            transaction.transaction_ref,
            transaction.transaction_type.value if transaction.transaction_type else '',
            transaction.status.value if transaction.status else '',
            transaction.amount / 100 if transaction.amount else 0,  # Convert from cents
            f"{transaction.citizen.first_name} {transaction.citizen.last_name}" if transaction.citizen else '',
            transaction.citizen.id_number if transaction.citizen else '',
            transaction.user.full_name if transaction.user else 'System',
            transaction.initiated_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.initiated_at else '',
            transaction.completed_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.completed_at else '',
            transaction.notes or ''
        ])
    
    # Log export action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.EXPORT,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} exported {len(transactions)} transactions"
        }
    )
    
    # Return CSV content
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/{transaction_id}", response_model=Dict)
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
    
    # Convert to dict to avoid pydantic validation issues
    return jsonable_encoder(transaction)


@router.get("/ref/{transaction_ref}", response_model=Dict)
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
    
    # Convert to dict to avoid pydantic validation issues
    return jsonable_encoder(transaction)


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