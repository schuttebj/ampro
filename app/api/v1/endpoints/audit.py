from typing import Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_superuser
from app.models.audit import ActionType, ResourceType
from app.models.user import User
from app.schemas.audit import AuditLog

router = APIRouter()


@router.get("/", response_model=List[AuditLog])
def read_audit_logs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve audit logs. Only accessible by superusers.
    """
    logs = crud.audit_log.get_multi(db, skip=skip, limit=limit)
    return logs


@router.get("/user/{user_id}", response_model=List[AuditLog])
def read_user_audit_logs(
    user_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve audit logs for a specific user. Only accessible by superusers.
    """
    logs = crud.audit_log.get_by_user_id(db, user_id=user_id, skip=skip, limit=limit)
    return logs


@router.get("/action/{action_type}", response_model=List[AuditLog])
def read_action_audit_logs(
    action_type: ActionType,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve audit logs for a specific action type. Only accessible by superusers.
    """
    logs = crud.audit_log.get_by_action_type(db, action_type=action_type, skip=skip, limit=limit)
    return logs


@router.get("/resource/{resource_type}", response_model=List[AuditLog])
def read_resource_audit_logs(
    resource_type: ResourceType,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve audit logs for a specific resource type. Only accessible by superusers.
    """
    logs = crud.audit_log.get_by_resource_type(db, resource_type=resource_type, skip=skip, limit=limit)
    return logs


@router.get("/resource/{resource_type}/{resource_id}", response_model=List[AuditLog])
def read_resource_id_audit_logs(
    resource_type: ResourceType,
    resource_id: str,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve audit logs for a specific resource. Only accessible by superusers.
    """
    logs = crud.audit_log.get_by_resource_id(
        db, resource_type=resource_type, resource_id=resource_id, skip=skip, limit=limit
    )
    return logs


@router.get("/date-range", response_model=List[AuditLog])
def read_date_range_audit_logs(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve audit logs within a date range. Only accessible by superusers.
    """
    if end_date is None:
        end_date = datetime.utcnow()
    
    logs = crud.audit_log.get_by_date_range(
        db, start_date=start_date, end_date=end_date, skip=skip, limit=limit
    )
    return logs 