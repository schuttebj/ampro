from typing import Any, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.audit import ActionType, ResourceType
from app.models.user import User
from app.models.license import ApplicationStatus, LicenseStatus, PrintJobStatus, ShippingStatus

router = APIRouter()


@router.get("/stats", response_model=Dict[str, Any])
def get_dashboard_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get comprehensive dashboard statistics.
    """
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    thirty_days_ago = today - timedelta(days=30)
    
    try:
        # Citizens Statistics
        total_citizens = db.query(func.count(crud.citizen.model.id)).scalar() or 0
        new_citizens_today = db.query(func.count(crud.citizen.model.id)).filter(
            func.date(crud.citizen.model.created_at) == today
        ).scalar() or 0
        active_citizens = db.query(func.count(crud.citizen.model.id)).filter(
            crud.citizen.model.is_active == True
        ).scalar() or 0

        # Applications Statistics
        total_applications = db.query(func.count(crud.license_application.model.id)).scalar() or 0
        pending_review = db.query(func.count(crud.license_application.model.id)).filter(
            or_(
                crud.license_application.model.status == ApplicationStatus.SUBMITTED,
                crud.license_application.model.status == ApplicationStatus.UNDER_REVIEW
            )
        ).scalar() or 0
        
        approved_today = db.query(func.count(crud.license_application.model.id)).filter(
            and_(
                crud.license_application.model.status == ApplicationStatus.APPROVED,
                func.date(crud.license_application.model.last_updated) == today
            )
        ).scalar() or 0
        
        rejected_today = db.query(func.count(crud.license_application.model.id)).filter(
            and_(
                crud.license_application.model.status == ApplicationStatus.REJECTED,
                func.date(crud.license_application.model.last_updated) == today
            )
        ).scalar() or 0
        
        pending_documents = db.query(func.count(crud.license_application.model.id)).filter(
            crud.license_application.model.status == ApplicationStatus.PENDING_DOCUMENTS
        ).scalar() or 0
        
        pending_payment = db.query(func.count(crud.license_application.model.id)).filter(
            crud.license_application.model.status == ApplicationStatus.PENDING_PAYMENT
        ).scalar() or 0

        # Licenses Statistics
        total_active_licenses = db.query(func.count(crud.license.model.id)).filter(
            crud.license.model.status == LicenseStatus.ACTIVE
        ).scalar() or 0
        
        issued_today = db.query(func.count(crud.license.model.id)).filter(
            func.date(crud.license.model.issue_date) == today
        ).scalar() or 0
        
        expiring_30_days = db.query(func.count(crud.license.model.id)).filter(
            and_(
                crud.license.model.expiry_date.between(today, today + timedelta(days=30)),
                crud.license.model.status == LicenseStatus.ACTIVE
            )
        ).scalar() or 0
        
        suspended_licenses = db.query(func.count(crud.license.model.id)).filter(
            crud.license.model.status == LicenseStatus.SUSPENDED
        ).scalar() or 0
        
        pending_collection = db.query(func.count(crud.license.model.id)).filter(
            crud.license.model.status == LicenseStatus.PENDING_COLLECTION
        ).scalar() or 0

        # Print Jobs Statistics
        queued_print_jobs = db.query(func.count(crud.print_job.model.id)).filter(
            crud.print_job.model.status == PrintJobStatus.QUEUED
        ).scalar() or 0
        
        printing_jobs = db.query(func.count(crud.print_job.model.id)).filter(
            crud.print_job.model.status == PrintJobStatus.PRINTING
        ).scalar() or 0
        
        completed_today = db.query(func.count(crud.print_job.model.id)).filter(
            and_(
                crud.print_job.model.status == PrintJobStatus.COMPLETED,
                func.date(crud.print_job.model.completed_at) == today
            )
        ).scalar() or 0
        
        failed_print_jobs = db.query(func.count(crud.print_job.model.id)).filter(
            crud.print_job.model.status == PrintJobStatus.FAILED
        ).scalar() or 0

        # Shipping Statistics  
        pending_shipping = db.query(func.count(crud.shipping_record.model.id)).filter(
            crud.shipping_record.model.status == ShippingStatus.PENDING
        ).scalar() or 0
        
        in_transit = db.query(func.count(crud.shipping_record.model.id)).filter(
            crud.shipping_record.model.status == ShippingStatus.IN_TRANSIT
        ).scalar() or 0
        
        delivered_today = db.query(func.count(crud.shipping_record.model.id)).filter(
            and_(
                crud.shipping_record.model.status == ShippingStatus.DELIVERED,
                func.date(crud.shipping_record.model.delivered_at) == today
            )
        ).scalar() or 0
        
        failed_shipping = db.query(func.count(crud.shipping_record.model.id)).filter(
            crud.shipping_record.model.status == ShippingStatus.FAILED
        ).scalar() or 0

        # Compliance Statistics (Mock for now - can be implemented based on ISO compliance data)
        iso_compliant_licenses = db.query(func.count(crud.license.model.id)).filter(
            and_(
                crud.license.model.iso_document_number.isnot(None),
                crud.license.model.iso_document_number != ""
            )
        ).scalar() or 0
        
        total_checked_licenses = total_active_licenses
        compliant_rate = (iso_compliant_licenses / total_checked_licenses * 100) if total_checked_licenses > 0 else 0
        critical_issues = 0  # This would be calculated based on actual compliance issues
        pending_validation = pending_review  # Approximate

        # System Performance (Mock data - can be implemented with actual monitoring)
        avg_processing_time = 2.5  # This would come from actual processing time tracking
        uptime_percentage = 99.8   # This would come from system monitoring
        
        # Determine queue health based on queue sizes
        total_queue_items = queued_print_jobs + pending_shipping + pending_review
        if total_queue_items < 50:
            queue_health = "good"
        elif total_queue_items < 150:
            queue_health = "warning"
        else:
            queue_health = "critical"

        # Log the dashboard access
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.READ,
                "resource_type": ResourceType.SYSTEM,
                "description": f"User {current_user.username} accessed dashboard statistics"
            }
        )

        return {
            "citizens": {
                "total": total_citizens,
                "new_today": new_citizens_today,
                "active": active_citizens
            },
            "applications": {
                "total": total_applications,
                "pending_review": pending_review,
                "approved_today": approved_today,
                "rejected_today": rejected_today,
                "pending_documents": pending_documents,
                "pending_payment": pending_payment
            },
            "licenses": {
                "total_active": total_active_licenses,
                "issued_today": issued_today,
                "expiring_30_days": expiring_30_days,
                "suspended": suspended_licenses,
                "pending_collection": pending_collection
            },
            "print_jobs": {
                "queued": queued_print_jobs,
                "printing": printing_jobs,
                "completed_today": completed_today,
                "failed": failed_print_jobs
            },
            "shipping": {
                "pending": pending_shipping,
                "in_transit": in_transit,
                "delivered_today": delivered_today,
                "failed": failed_shipping
            },
            "compliance": {
                "compliant_rate": round(compliant_rate, 1),
                "critical_issues": critical_issues,
                "pending_validation": pending_validation
            },
            "system_performance": {
                "avg_processing_time": avg_processing_time,
                "uptime_percentage": uptime_percentage,
                "queue_health": queue_health
            },
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard statistics: {str(e)}"
        )


@router.get("/recent-activities", response_model=Dict[str, Any])
def get_recent_activities(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = 10,
) -> Any:
    """
    Get recent system activities for dashboard.
    """
    try:
        # Get recent audit logs
        recent_logs = (
            db.query(crud.audit_log.model)
            .filter(crud.audit_log.model.user_id.isnot(None))  # Only user actions, not system actions
            .order_by(crud.audit_log.model.created_at.desc())
            .limit(limit)
            .all()
        )

        activities = []
        for log in recent_logs:
            user = crud.user.get(db, id=log.user_id) if log.user_id else None
            
            # Map resource types to activity types
            activity_type_map = {
                ResourceType.APPLICATION: "application",
                ResourceType.LICENSE: "license", 
                ResourceType.CITIZEN: "citizen",
                ResourceType.PRINT_JOB: "print",
                ResourceType.SHIPPING: "shipping",
                ResourceType.USER: "user",
                ResourceType.SYSTEM: "system"
            }
            
            # Map action types to status
            status_map = {
                ActionType.CREATE: "success",
                ActionType.UPDATE: "info",
                ActionType.DELETE: "warning",
                ActionType.READ: "info"
            }

            activities.append({
                "id": log.id,
                "type": activity_type_map.get(log.resource_type, "system"),
                "action": log.description,
                "entity_id": log.resource_id or "N/A",
                "user": user.full_name if user else "System",
                "timestamp": log.created_at.isoformat(),
                "status": status_map.get(log.action_type, "info"),
                "details": log.description
            })

        return {
            "activities": activities,
            "total": len(activities),
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recent activities: {str(e)}"
        )


@router.get("/system-alerts", response_model=Dict[str, Any])
def get_system_alerts(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get system alerts for dashboard.
    """
    try:
        alerts = []
        
        # Check for high queue volumes
        pending_apps = db.query(func.count(crud.license_application.model.id)).filter(
            crud.license_application.model.status == ApplicationStatus.SUBMITTED
        ).scalar() or 0
        
        if pending_apps > 100:
            alerts.append({
                "id": "high_queue_apps",
                "type": "warning",
                "title": "High Application Queue",
                "message": f"{pending_apps} applications pending review. Consider increasing processing capacity.",
                "timestamp": datetime.utcnow().isoformat(),
                "actionUrl": "/workflow/applications",
                "actionLabel": "Review Applications",
                "dismissible": True
            })

        # Check for expiring licenses
        expiring_soon = db.query(func.count(crud.license.model.id)).filter(
            and_(
                crud.license.model.expiry_date.between(
                    datetime.utcnow().date(),
                    datetime.utcnow().date() + timedelta(days=7)
                ),
                crud.license.model.status == LicenseStatus.ACTIVE
            )
        ).scalar() or 0
        
        if expiring_soon > 50:
            alerts.append({
                "id": "expiring_licenses",
                "type": "warning", 
                "title": "Licenses Expiring Soon",
                "message": f"{expiring_soon} licenses expiring within 7 days.",
                "timestamp": datetime.utcnow().isoformat(),
                "actionUrl": "/licenses",
                "actionLabel": "View Licenses",
                "dismissible": True
            })

        # Check print job failures
        if hasattr(crud, 'print_job'):
            failed_jobs = db.query(func.count(crud.print_job.model.id)).filter(
                crud.print_job.model.status == PrintJobStatus.FAILED
            ).scalar() or 0
            
            if failed_jobs > 5:
                alerts.append({
                    "id": "print_failures",
                    "type": "error",
                    "title": "Print Job Failures",
                    "message": f"{failed_jobs} print jobs have failed. Hardware intervention may be required.",
                    "timestamp": datetime.utcnow().isoformat(),
                    "actionUrl": "/workflow/print-queue",
                    "actionLabel": "Check Print Queue",
                    "dismissible": False
                })

        # System maintenance notice (mock)
        alerts.append({
            "id": "maintenance_notice",
            "type": "info",
            "title": "Scheduled Maintenance",
            "message": "System maintenance scheduled for Sunday 2:00 AM - 4:00 AM.",
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "dismissible": True
        })

        return {
            "alerts": alerts,
            "total": len(alerts),
            "critical_count": len([a for a in alerts if a["type"] == "error"]),
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system alerts: {str(e)}"
        ) 