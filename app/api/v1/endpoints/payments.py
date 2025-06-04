from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType, TransactionType as AuditTransactionType, TransactionStatus
from app.models.license import PaymentStatus, PaymentMethod
from app.models.user import User
from app.schemas.license import (
    Payment, 
    PaymentCreate, 
    PaymentUpdate
)

router = APIRouter()


@router.get("/", response_model=List[Payment])
def read_payments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    application_id: int = None,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve payments with optional filtering.
    """
    query_filters = {}
    
    if application_id:
        payments = crud.payment.get_by_application_id(db, application_id=application_id)
    elif status:
        try:
            status_enum = PaymentStatus(status)
            if status_enum == PaymentStatus.PENDING:
                payments = crud.payment.get_pending_payments(db, skip=skip, limit=limit)
            else:
                payments = crud.payment.get_multi(db, skip=skip, limit=limit)
                payments = [p for p in payments if p.status == status_enum]
        except ValueError:
            payments = crud.payment.get_multi(db, skip=skip, limit=limit)
    else:
        payments = crud.payment.get_multi(db, skip=skip, limit=limit)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.PAYMENT,
            "description": f"User {current_user.username} retrieved list of payments"
        }
    )
    
    return payments


@router.post("/", response_model=Payment)
def create_payment(
    *,
    db: Session = Depends(get_db),
    payment_in: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new payment for an application.
    """
    # Check if application exists
    application = crud.license_application.get(db, id=payment_in.application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    
    # Generate payment reference if not provided
    payment_data = jsonable_encoder(payment_in)
    if not payment_data.get("payment_reference"):
        payment_data["payment_reference"] = crud.payment.generate_payment_reference(db)
    
    # Create payment
    payment = crud.payment.create(db, obj_in=payment_data)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.PAYMENT,
            "resource_id": str(payment.id),
            "description": f"User {current_user.username} created payment {payment.payment_reference} for application {application.id}"
        }
    )
    
    return payment


@router.get("/search", response_model=List[Dict])
def search_payment(
    db: Session = Depends(get_db),
    q: str = None,
    application_id: int = None,
    citizen_id: str = None,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Search for payments by application ID, citizen ID, or payment reference.
    """
    results = []
    
    if q:
        # Search by payment reference
        payment = crud.payment.get_by_reference(db, payment_reference=q)
        if payment:
            application = crud.license_application.get(db, id=payment.application_id)
            citizen = crud.citizen.get(db, id=application.citizen_id) if application else None
            
            result = jsonable_encoder(payment)
            result["application"] = jsonable_encoder(application) if application else None
            result["citizen"] = jsonable_encoder(citizen) if citizen else None
            results.append(result)
    
    if application_id:
        # Search by application ID
        payments = crud.payment.get_by_application_id(db, application_id=application_id)
        for payment in payments:
            application = crud.license_application.get(db, id=payment.application_id)
            citizen = crud.citizen.get(db, id=application.citizen_id) if application else None
            
            result = jsonable_encoder(payment)
            result["application"] = jsonable_encoder(application) if application else None
            result["citizen"] = jsonable_encoder(citizen) if citizen else None
            results.append(result)
    
    if citizen_id:
        # Search by citizen ID
        citizen = crud.citizen.get_by_id_number(db, id_number=citizen_id)
        if citizen:
            applications = crud.license_application.get_by_citizen_id(db, citizen_id=citizen.id)
            for application in applications:
                payments = crud.payment.get_by_application_id(db, application_id=application.id)
                for payment in payments:
                    result = jsonable_encoder(payment)
                    result["application"] = jsonable_encoder(application)
                    result["citizen"] = jsonable_encoder(citizen)
                    results.append(result)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.PAYMENT,
            "description": f"User {current_user.username} searched payments with query: {q}, application_id: {application_id}, citizen_id: {citizen_id}"
        }
    )
    
    return results


@router.get("/{payment_id}", response_model=Dict)
def read_payment(
    *,
    db: Session = Depends(get_db),
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get payment by ID with related information.
    """
    payment = crud.payment.get(db, id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    # Get related data
    application = crud.license_application.get(db, id=payment.application_id) if payment.application_id else None
    citizen = crud.citizen.get(db, id=application.citizen_id) if application else None
    processed_by = crud.user.get(db, id=payment.processed_by_user_id) if payment.processed_by_user_id else None
    
    result = jsonable_encoder(payment)
    result["application"] = jsonable_encoder(application) if application else None
    result["citizen"] = jsonable_encoder(citizen) if citizen else None
    result["processed_by"] = jsonable_encoder(processed_by) if processed_by else None
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.PAYMENT,
            "resource_id": str(payment.id),
            "description": f"User {current_user.username} viewed payment {payment.payment_reference}"
        }
    )
    
    return result


@router.put("/{payment_id}", response_model=Payment)
def update_payment(
    *,
    db: Session = Depends(get_db),
    payment_id: int,
    payment_in: PaymentUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a payment.
    """
    payment = crud.payment.get(db, id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    payment = crud.payment.update(db, db_obj=payment, obj_in=payment_in)
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.PAYMENT,
            "resource_id": str(payment.id),
            "description": f"User {current_user.username} updated payment {payment.payment_reference}"
        }
    )
    
    return payment


@router.post("/{payment_id}/mark-paid", response_model=Payment)
def mark_payment_as_paid(
    *,
    db: Session = Depends(get_db),
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Mark a payment as paid.
    """
    payment = crud.payment.get(db, id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    if payment.status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is already marked as paid",
        )
    
    payment = crud.payment.mark_as_paid(db, payment_id=payment_id, processed_by_user_id=current_user.id)
    
    # Update application payment status
    if payment.application_id:
        application = crud.license_application.get(db, id=payment.application_id)
        if application:
            application.payment_verified = True
            application.payment_reference = payment.payment_reference
            if application.status == "pending_payment":
                application.status = "submitted"
            crud.license_application.update(db, db_obj=application, obj_in={})
    
    # Log action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.PAYMENT,
            "resource_id": str(payment.id),
            "description": f"User {current_user.username} marked payment {payment.payment_reference} as paid"
        }
    )
    
    return payment 