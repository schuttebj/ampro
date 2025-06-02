from typing import Any, List
from datetime import datetime, timedelta
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session, joinedload

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_superuser
from app.models.audit import ActionType, ResourceType, AuditLog
from app.models.user import User
from app.schemas.audit import AuditLog as AuditLogSchema

router = APIRouter()


@router.get("/")
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
    # Build base query with relationships
    query = db.query(AuditLog).options(joinedload(AuditLog.user))
    
    # Apply filters
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)
    if date_from:
        date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        query = query.filter(AuditLog.timestamp >= date_from_parsed)
    if date_to:
        date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        query = query.filter(AuditLog.timestamp <= date_to_parsed)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    # Convert to dict format that frontend expects
    items = []
    for log in logs:
        item = {
            "id": log.id,
            "user_id": log.user_id,
            "action_type": log.action_type.value if log.action_type else None,
            "resource_type": log.resource_type.value if log.resource_type else None,
            "resource_id": log.resource_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "description": log.description,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "user": {
                "id": log.user.id,
                "full_name": log.user.full_name,
                "username": log.user.username
            } if log.user else None
        }
        items.append(item)
    
    # Return paginated response
    return {
        "items": items,
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }


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


@router.get("/user/{user_id}", response_model=List[AuditLogSchema])
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


@router.get("/action/{action_type}", response_model=List[AuditLogSchema])
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


@router.get("/resource/{resource_type}", response_model=List[AuditLogSchema])
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


@router.get("/resource/{resource_type}/{resource_id}", response_model=List[AuditLogSchema])
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


@router.get("/date-range", response_model=List[AuditLogSchema])
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