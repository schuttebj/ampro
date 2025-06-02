from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.notification import NotificationCategory, NotificationPriority, NotificationStatus
from app.schemas.notification import (
    Notification, NotificationCreate, NotificationUpdate, 
    NotificationBulkUpdate, NotificationStats, 
    NotificationPreference, NotificationPreferenceUpdate, NotificationPreferenceCreate
)
from app.services.notification_service import NotificationService
from app.models.audit import ActionType, ResourceType

router = APIRouter()

# WebSocket connection manager for real-time notifications
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_notification(self, user_id: int, notification: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(notification)
            except:
                # Connection broken, remove it
                self.disconnect(user_id)

manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications
    (New functionality, extends existing real-time capabilities)
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)


@router.get("/", response_model=List[Notification])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 50,
    status: Optional[NotificationStatus] = None,
    category: Optional[NotificationCategory] = None,
    priority: Optional[NotificationPriority] = None,
) -> Any:
    """
    Get user's notifications with filtering
    (Integrates with existing auth and pagination patterns)
    """
    notification_service = NotificationService(db)
    notifications = notification_service.get_user_notifications(
        user_id=current_user.id,
        status=status,
        category=category,
        priority=priority,
        limit=limit
    )
    
    # Log action using existing audit system
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.READ,
            "resource_type": ResourceType.SYSTEM,  # Changed from NOTIFICATION to SYSTEM
            "description": f"User {current_user.username} retrieved notifications"
        }
    )
    
    return notifications


@router.get("/stats", response_model=NotificationStats)
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get notification statistics for the current user
    """
    notification_service = NotificationService(db)
    stats = notification_service.get_notification_stats(current_user.id)
    
    return stats


@router.put("/{notification_id}/read", response_model=dict)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Mark a notification as read
    (Uses existing auth patterns for user ownership)
    """
    notification_service = NotificationService(db)
    success = notification_service.mark_as_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )
    
    # Log action using existing audit system
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.SYSTEM,  # Changed from NOTIFICATION to SYSTEM
            "resource_id": str(notification_id),
            "description": f"User {current_user.username} marked notification as read"
        }
    )
    
    return {"message": "Notification marked as read", "success": True}


@router.put("/bulk", response_model=dict)
def bulk_update_notifications(
    bulk_update: NotificationBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Bulk update notifications (mark as read, archive, etc.)
    """
    notification_service = NotificationService(db)
    
    status_mapping = {
        "mark_read": NotificationStatus.READ,
        "archive": NotificationStatus.ARCHIVED,
        "delete": NotificationStatus.DISMISSED
    }
    
    if bulk_update.action not in status_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {bulk_update.action}"
        )
    
    updated_count = notification_service.bulk_update_status(
        notification_ids=bulk_update.notification_ids,
        status=status_mapping[bulk_update.action],
        user_id=current_user.id
    )
    
    # Log bulk action using existing audit system
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.SYSTEM,  # Changed from NOTIFICATION to SYSTEM
            "description": f"User {current_user.username} performed bulk {bulk_update.action} on {updated_count} notifications"
        }
    )
    
    return {
        "message": f"Updated {updated_count} notifications",
        "updated_count": updated_count,
        "action": bulk_update.action
    }


@router.get("/preferences", response_model=NotificationPreference)
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get user's notification preferences
    """
    preferences = crud.notification_preference.get_by_user_id(db, user_id=current_user.id)
    
    if not preferences:
        # Create default preferences if none exist
        default_prefs = NotificationPreferenceCreate(user_id=current_user.id)
        preferences = crud.notification_preference.create(db, obj_in=default_prefs)
    
    return preferences


@router.put("/preferences", response_model=NotificationPreference)
def update_notification_preferences(
    preferences_update: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update user's notification preferences
    """
    preferences = crud.notification_preference.get_by_user_id(db, user_id=current_user.id)
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preferences not found"
        )
    
    updated_preferences = crud.notification_preference.update(
        db, db_obj=preferences, obj_in=preferences_update
    )
    
    # Log action using existing audit system
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.UPDATE,
            "resource_type": ResourceType.USER,
            "resource_id": str(current_user.id),
            "description": f"User {current_user.username} updated notification preferences"
        }
    )
    
    return updated_preferences


@router.post("/workflow", response_model=Notification)
def create_workflow_notification(
    notification_create: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a workflow notification (for system integrations)
    """
    notification_service = NotificationService(db)
    
    # Add the triggering user
    notification_create.triggered_by_user_id = current_user.id
    
    notification = crud.notification.create(db, obj_in=notification_create)
    
    # Send real-time notification if user is connected
    if notification.user_id and notification.user_id in manager.active_connections:
        import asyncio
        asyncio.create_task(
            manager.send_personal_notification(
                notification.user_id,
                {
                    "event_type": "new_notification",
                    "notification": notification.__dict__
                }
            )
        )
    
    # Log action using existing audit system
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.SYSTEM,  # Changed from NOTIFICATION to SYSTEM
            "resource_id": str(notification.id),
            "description": f"Workflow notification created by {current_user.username}"
        }
    )
    
    return notification


# Integration endpoints for basic workflow events
@router.post("/trigger/application-approved/{application_id}")
def trigger_application_approved(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Trigger notification when application is approved
    (Integrates with existing application workflow)
    """
    application = crud.license_application.get(db, id=application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    notification_service = NotificationService(db)
    
    # Create notification for citizen (if they have a user account)
    citizen = crud.citizen.get(db, id=application.citizen_id)
    if citizen and citizen.user_id:
        notification = notification_service.create_workflow_notification(
            category=NotificationCategory.APPLICATION,
            title="License Application Approved",
            message=f"Your license application has been approved and forwarded to print queue.",
            priority=NotificationPriority.NORMAL,
            user_id=citizen.user_id,
            entity_type="application",
            entity_id=application.id,
            action_url="/workflow/applications"
        )
        
        # Send real-time notification
        if citizen.user_id in manager.active_connections:
            import asyncio
            asyncio.create_task(
                manager.send_personal_notification(
                    citizen.user_id,
                    {
                        "event_type": "new_notification",
                        "notification": notification.__dict__
                    }
                )
            )
    
    return {"message": "Application approval notification sent", "success": True}


@router.post("/trigger/print-completed/{batch_id}")
def trigger_print_completed(
    batch_id: str,
    success_count: int,
    failure_count: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Trigger notification when print batch is completed
    (Integrates with existing print workflow)
    """
    notification_service = NotificationService(db)
    
    # Determine notification type and priority based on results
    if failure_count > 0:
        notification_type = NotificationPriority.HIGH
        title = "Print Batch Completed with Errors"
        message = f"Print batch {batch_id}: {success_count} successful, {failure_count} failed"
    else:
        notification_type = NotificationPriority.NORMAL
        title = "Print Batch Completed Successfully"
        message = f"Print batch {batch_id}: {success_count} licenses printed successfully"
    
    # Create notification for print operators (users with printer role)
    printer_users = crud.user.get_users_by_role(db, role_name="printer")
    
    for user in printer_users:
        notification = notification_service.create_workflow_notification(
            category=NotificationCategory.PRINT_JOB,
            title=title,
            message=message,
            priority=notification_type,
            user_id=user.id,
            entity_type="print_batch",
            entity_id=batch_id,
            action_url="/workflow/print-queue",
            metadata={"success_count": success_count, "failure_count": failure_count}
        )
    
    return {"message": "Print completion notifications sent", "success": True}


# AUTOMATION NOTIFICATION ENDPOINTS
@router.post("/automation/batch-processing", response_model=dict)
def create_batch_processing_notification(
    batch_type: str,
    application_ids: List[int],
    collection_point: Optional[str] = None,
    preview_mode: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create notification for batch processing operations
    (Integrates with automation features)
    """
    notification_service = NotificationService(db)
    
    # Create notification using the unified service
    notification = notification_service.create_batch_processing_notification(
        batch_type=batch_type,
        application_ids=application_ids,
        collection_point=collection_point,
        user_id=current_user.id,
        initiated_by_user_id=current_user.id,
        preview_mode=preview_mode
    )
    
    # Log action using existing audit system
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": current_user.id,
            "action_type": ActionType.CREATE,
            "resource_type": ResourceType.SYSTEM,
            "resource_id": str(notification.id),
            "description": f"Batch processing notification created for {batch_type}"
        }
    )
    
    return {
        "message": "Batch processing notification created",
        "notification_id": notification.id,
        "batch_type": batch_type,
        "applications_processed": len(application_ids),
        "success": True
    }


@router.post("/automation/rule-engine", response_model=dict)
def create_rule_engine_notification(
    rule_name: str,
    rule_action: str,  # 'applied', 'failed', 'disabled'
    application_ids: List[int],
    details: Optional[str] = None,
    notify_all_admins: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create notification for rule engine actions
    (Integrates with rule-based automation)
    """
    notification_service = NotificationService(db)
    
    # Determine who to notify
    if notify_all_admins:
        admin_users = crud.user.get_users_by_role(db, role_name="admin")
        target_users = admin_users
    else:
        target_users = [current_user]
    
    notifications_created = []
    for user in target_users:
        notification = notification_service.create_rule_engine_notification(
            rule_name=rule_name,
            rule_action=rule_action,
            application_ids=application_ids,
            details=details,
            user_id=user.id
        )
        notifications_created.append(notification.id)
    
    return {
        "message": "Rule engine notifications created",
        "notification_ids": notifications_created,
        "rule_name": rule_name,
        "rule_action": rule_action,
        "affected_count": len(application_ids),
        "success": True
    }


@router.post("/automation/smart-assignment", response_model=dict)
def create_smart_assignment_notification(
    assignment_type: str,  # 'printer', 'user', 'location'
    assignment_criteria: Dict[str, Any],
    application_ids: Optional[List[int]] = None,
    notify_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create notification for smart assignment operations
    """
    notification_service = NotificationService(db)
    
    target_user_id = notify_user_id or current_user.id
    
    notification = notification_service.create_smart_assignment_notification(
        assignment_type=assignment_type,
        assignment_criteria=assignment_criteria,
        application_ids=application_ids,
        user_id=target_user_id
    )
    
    return {
        "message": "Smart assignment notification created",
        "notification_id": notification.id,
        "assignment_type": assignment_type,
        "success": True
    }


@router.get("/automation/stats", response_model=dict)
def get_automation_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get automation notification statistics
    """
    # Get automation-related notifications for the user
    automation_notifications = db.query(crud.notification.model)\
        .filter(
            crud.notification.model.user_id == current_user.id,
            crud.notification.model.category.in_([
                "AUTOMATION", "BATCH_PROCESSING", "RULE_ENGINE"
            ])
        )\
        .all()
    
    stats = {
        "total_automation_notifications": len(automation_notifications),
        "batch_processing_count": len([n for n in automation_notifications if n.category == "BATCH_PROCESSING"]),
        "rule_engine_count": len([n for n in automation_notifications if n.category == "RULE_ENGINE"]),
        "automation_count": len([n for n in automation_notifications if n.category == "AUTOMATION"]),
        "unread_automation": len([n for n in automation_notifications if n.status == "unread"]),
        "recent_automations": [
            {
                "id": n.id,
                "title": n.title,
                "category": n.category,
                "priority": n.priority,
                "created_at": n.created_at.isoformat()
            }
            for n in sorted(automation_notifications, key=lambda x: x.created_at, reverse=True)[:5]
        ]
    }
    
    return stats


# ISO COMPLIANCE NOTIFICATION ENDPOINTS
@router.post("/iso/compliance-validation", response_model=dict)
def create_iso_compliance_notification(
    license_id: int,
    iso_standard: str = "ISO_18013_1",
    full_validation: bool = True,
    notify_user_id: Optional[int] = None,
    notify_compliance_officers: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create notification for ISO compliance validation
    (Integrates with ISO compliance features)
    """
    license_record = crud.license.get(db, id=license_id)
    if not license_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    notification_service = NotificationService(db)
    
    # Create primary notification
    target_user_id = notify_user_id or current_user.id
    notification = notification_service.create_iso_compliance_notification(
        license_id=license_id,
        iso_standard=iso_standard,
        user_id=target_user_id,
        full_validation=full_validation
    )
    
    notifications_created = [notification.id]
    
    # For critical failures, also notify compliance officers
    if notify_compliance_officers and notification.priority == NotificationPriority.CRITICAL:
        compliance_users = crud.user.get_users_by_role(db, role_name="admin")
        for user in compliance_users:
            if user.id != target_user_id:  # Don't duplicate
                additional_notification = notification_service.create_iso_compliance_notification(
                    license_id=license_id,
                    iso_standard=iso_standard,
                    user_id=user.id,
                    full_validation=full_validation
                )
                notifications_created.append(additional_notification.id)
    
    return {
        "message": "ISO compliance notifications created",
        "notification_ids": notifications_created,
        "license_id": license_id,
        "iso_standard": iso_standard,
        "success": True
    }


@router.post("/iso/validation", response_model=dict)
def create_validation_notification(
    entity_type: str,  # 'license', 'application', 'citizen'
    entity_id: int,
    validation_type: str,  # 'mrz', 'biometric', 'security_features', 'chip_data'
    iso_reference: Optional[str] = None,
    notify_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create notification for validation processes
    (Integrates with validation systems)
    """
    notification_service = NotificationService(db)
    
    target_user_id = notify_user_id or current_user.id
    
    notification = notification_service.create_validation_notification(
        validation_type=validation_type,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=target_user_id,
        iso_reference=iso_reference
    )
    
    return {
        "message": "Validation notification created",
        "notification_id": notification.id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "validation_type": validation_type,
        "success": True
    }


@router.post("/iso/bulk-compliance", response_model=dict)
def create_bulk_compliance_notification(
    operation_type: str,  # 'bulk_validation', 'bulk_remediation'
    license_ids: List[int],
    iso_standards: List[str],
    notify_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create notification for bulk ISO compliance operations
    """
    notification_service = NotificationService(db)
    
    target_user_id = notify_user_id or current_user.id
    
    notification = notification_service.create_bulk_compliance_notification(
        operation_type=operation_type,
        license_ids=license_ids,
        iso_standards=iso_standards,
        user_id=target_user_id
    )
    
    return {
        "message": "Bulk compliance notification created",
        "notification_id": notification.id,
        "operation_type": operation_type,
        "licenses_processed": len(license_ids),
        "iso_standards": iso_standards,
        "success": True
    }


@router.post("/iso/auto-remediation", response_model=dict)
def create_auto_remediation_notification(
    license_id: int,
    notify_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create notification for auto-remediation processes
    """
    license_record = crud.license.get(db, id=license_id)
    if not license_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    
    notification_service = NotificationService(db)
    
    target_user_id = notify_user_id or current_user.id
    
    notification = notification_service.create_auto_remediation_notification(
        license_id=license_id,
        user_id=target_user_id
    )
    
    return {
        "message": "Auto-remediation notification created",
        "notification_id": notification.id,
        "license_id": license_id,
        "success": True
    }


@router.get("/iso/compliance-stats", response_model=dict)
def get_iso_compliance_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get ISO compliance notification statistics
    """
    # Get ISO compliance-related notifications for the user
    iso_notifications = db.query(crud.notification.model)\
        .filter(
            crud.notification.model.user_id == current_user.id,
            crud.notification.model.category.in_([
                "ISO_COMPLIANCE", "VALIDATION"
            ])
        )\
        .all()
    
    stats = {
        "total_iso_notifications": len(iso_notifications),
        "iso_compliance_count": len([n for n in iso_notifications if n.category == "ISO_COMPLIANCE"]),
        "validation_count": len([n for n in iso_notifications if n.category == "VALIDATION"]),
        "critical_failures": len([n for n in iso_notifications if n.priority == "CRITICAL"]),
        "unread_iso": len([n for n in iso_notifications if n.status == "unread"]),
        "compliance_breakdown": {
            "critical": len([n for n in iso_notifications if n.priority == "CRITICAL"]),
            "high": len([n for n in iso_notifications if n.priority == "HIGH"]),
            "normal": len([n for n in iso_notifications if n.priority == "NORMAL"]),
            "low": len([n for n in iso_notifications if n.priority == "LOW"])
        },
        "recent_compliance": [
            {
                "id": n.id,
                "title": n.title,
                "category": n.category,
                "priority": n.priority,
                "created_at": n.created_at.isoformat(),
                "metadata": n.metadata
            }
            for n in sorted(iso_notifications, key=lambda x: x.created_at, reverse=True)[:5]
        ]
    }
    
    return stats 