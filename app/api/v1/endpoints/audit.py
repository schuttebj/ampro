from typing import Any, List
from datetime import datetime, timedelta
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
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
    user_id: int = None,
    action_type: ActionType = None,
    resource_type: ResourceType = None,
    resource_id: str = None,
    date_from: str = None,
    date_to: str = None,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve audit logs with filtering. Only accessible by superusers.
    """
    # Build filters and apply them
    if user_id:
        logs = crud.audit_log.get_by_user_id(db, user_id=user_id, skip=skip, limit=limit)
    elif action_type:
        logs = crud.audit_log.get_by_action_type(db, action_type=action_type, skip=skip, limit=limit)
    elif resource_type and resource_id:
        logs = crud.audit_log.get_by_resource_id(db, resource_type=resource_type, resource_id=resource_id, skip=skip, limit=limit)
    elif resource_type:
        logs = crud.audit_log.get_by_resource_type(db, resource_type=resource_type, skip=skip, limit=limit)
    elif date_from and date_to:
        start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        logs = crud.audit_log.get_by_date_range(db, start_date=start_date, end_date=end_date, skip=skip, limit=limit)
    else:
        logs = crud.audit_log.get_multi(db, skip=skip, limit=limit)
    
    return logs


@router.get("/export")
def export_audit_logs(
    db: Session = Depends(get_db),
    user_id: int = None,
    action_type: ActionType = None,
    resource_type: ResourceType = None,
    date_from: str = None,
    date_to: str = None,
    format: str = Query(default="csv", regex="^(csv|excel)$"),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Export audit logs to CSV or Excel. Only accessible by superusers.
    """
    # Get audit logs based on filters (remove limit for export)
    if user_id:
        logs = crud.audit_log.get_by_user_id(db, user_id=user_id, skip=0, limit=50000)
    elif action_type:
        logs = crud.audit_log.get_by_action_type(db, action_type=action_type, skip=0, limit=50000)
    elif resource_type:
        logs = crud.audit_log.get_by_resource_type(db, resource_type=resource_type, skip=0, limit=50000)
    elif date_from and date_to:
        start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        logs = crud.audit_log.get_by_date_range(db, start_date=start_date, end_date=end_date, skip=0, limit=50000)
    else:
        logs = crud.audit_log.get_multi(db, skip=0, limit=50000)
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Timestamp',
        'User',
        'Action Type',
        'Resource Type',
        'Resource ID',
        'Description',
        'IP Address',
        'User Agent'
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
            log.user.full_name if log.user else 'System',
            log.action_type.value if log.action_type else '',
            log.resource_type.value if log.resource_type else '',
            log.resource_id or '',
            log.description or '',
            log.ip_address or '',
            log.user_agent or ''
        ])
    
    # Log export action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.EXPORT,
            "resource_type": ResourceType.SYSTEM,
            "description": f"User {current_user.username} exported {len(logs)} audit logs"
        }
    )
    
    # Return CSV content
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


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