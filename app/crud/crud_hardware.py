from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.crud.base import CRUDBase
from app.models.hardware import Hardware, HardwareType, HardwareStatus
from app.schemas.hardware import HardwareCreate, HardwareUpdate


class CRUDHardware(CRUDBase[Hardware, HardwareCreate, HardwareUpdate]):
    """CRUD operations for Hardware model."""

    def get_by_code(self, db: Session, *, code: str) -> Optional[Hardware]:
        """Get hardware by code."""
        return db.query(Hardware).filter(Hardware.code == code).first()

    def get_by_location(
        self, 
        db: Session, 
        *, 
        location_id: int, 
        hardware_type: Optional[HardwareType] = None,
        status: Optional[HardwareStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Hardware]:
        """Get hardware by location, optionally filtered by type and status."""
        query = db.query(Hardware).filter(Hardware.location_id == location_id)
        
        if hardware_type:
            query = query.filter(Hardware.hardware_type == hardware_type)
        
        if status:
            query = query.filter(Hardware.status == status)
        
        return query.offset(skip).limit(limit).all()

    def get_by_type(
        self, 
        db: Session, 
        *, 
        hardware_type: HardwareType,
        status: Optional[HardwareStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Hardware]:
        """Get hardware by type, optionally filtered by status."""
        query = db.query(Hardware).filter(Hardware.hardware_type == hardware_type)
        
        if status:
            query = query.filter(Hardware.status == status)
        
        return query.offset(skip).limit(limit).all()

    def get_available_webcams(
        self, 
        db: Session, 
        *, 
        location_id: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Hardware]:
        """Get available webcams for photo capture."""
        query = db.query(Hardware).filter(
            and_(
                Hardware.hardware_type == HardwareType.WEBCAM,
                Hardware.status == HardwareStatus.ACTIVE
            )
        )
        
        if location_id:
            query = query.filter(Hardware.location_id == location_id)
        
        return query.offset(skip).limit(limit).all()

    def search_hardware(
        self,
        db: Session,
        *,
        search_term: str,
        location_id: Optional[int] = None,
        hardware_type: Optional[HardwareType] = None,
        status: Optional[HardwareStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Hardware]:
        """Search hardware by name, code, model, or manufacturer."""
        query = db.query(Hardware)
        
        # Build search conditions
        search_conditions = []
        if search_term:
            search_term = f"%{search_term}%"
            search_conditions.append(
                or_(
                    Hardware.name.ilike(search_term),
                    Hardware.code.ilike(search_term),
                    Hardware.model.ilike(search_term),
                    Hardware.manufacturer.ilike(search_term),
                    Hardware.serial_number.ilike(search_term)
                )
            )
        
        # Apply filters
        conditions = []
        if search_conditions:
            conditions.extend(search_conditions)
        
        if location_id:
            conditions.append(Hardware.location_id == location_id)
        
        if hardware_type:
            conditions.append(Hardware.hardware_type == hardware_type)
        
        if status:
            conditions.append(Hardware.status == status)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        return query.offset(skip).limit(limit).all()

    def update_status(
        self,
        db: Session,
        *,
        hardware_id: int,
        status: HardwareStatus,
        notes: Optional[str] = None
    ) -> Optional[Hardware]:
        """Update hardware status."""
        hardware_obj = self.get(db, id=hardware_id)
        if not hardware_obj:
            return None
        
        update_data = {"status": status}
        if notes:
            existing_notes = hardware_obj.notes or ""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_note = f"[{timestamp}] Status changed to {status.value}: {notes}"
            update_data["notes"] = f"{existing_notes}\n{new_note}".strip()
        
        return self.update(db, db_obj=hardware_obj, obj_in=update_data)

    def record_usage(
        self,
        db: Session,
        *,
        hardware_id: int,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Optional[Hardware]:
        """Record hardware usage and update statistics."""
        hardware_obj = self.get(db, id=hardware_id)
        if not hardware_obj:
            return None
        
        update_data = {
            "last_used": datetime.now(),
            "usage_count": hardware_obj.usage_count + 1
        }
        
        if not success:
            update_data["error_count"] = hardware_obj.error_count + 1
            update_data["last_error"] = error_message
            update_data["last_error_time"] = datetime.now()
        
        return self.update(db, db_obj=hardware_obj, obj_in=update_data)

    def update_online_status(
        self,
        db: Session,
        *,
        hardware_id: int,
        is_online: bool = True
    ) -> Optional[Hardware]:
        """Update hardware online status."""
        hardware_obj = self.get(db, id=hardware_id)
        if not hardware_obj:
            return None
        
        update_data = {}
        if is_online:
            update_data["last_online"] = datetime.now()
            # If hardware was offline/error, set to active
            if hardware_obj.status in [HardwareStatus.OFFLINE, HardwareStatus.ERROR]:
                update_data["status"] = HardwareStatus.ACTIVE
        else:
            update_data["status"] = HardwareStatus.OFFLINE
        
        return self.update(db, db_obj=hardware_obj, obj_in=update_data)

    def get_maintenance_due(
        self, 
        db: Session, 
        *, 
        days_ahead: int = 7,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Hardware]:
        """Get hardware that needs maintenance soon."""
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        return (
            db.query(Hardware)
            .filter(
                and_(
                    Hardware.next_maintenance.isnot(None),
                    Hardware.next_maintenance <= cutoff_date,
                    Hardware.status != HardwareStatus.MAINTENANCE
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get hardware statistics."""
        # Count by status
        status_counts = (
            db.query(Hardware.status, func.count(Hardware.id))
            .group_by(Hardware.status)
            .all()
        )
        
        # Count by type
        type_counts = (
            db.query(Hardware.hardware_type, func.count(Hardware.id))
            .group_by(Hardware.hardware_type)
            .all()
        )
        
        # Count by location
        location_counts = (
            db.query(Hardware.location_id, func.count(Hardware.id))
            .group_by(Hardware.location_id)
            .all()
        )
        
        # Total counts
        total = db.query(func.count(Hardware.id)).scalar()
        active = db.query(func.count(Hardware.id)).filter(Hardware.status == HardwareStatus.ACTIVE).scalar()
        offline = db.query(func.count(Hardware.id)).filter(Hardware.status == HardwareStatus.OFFLINE).scalar()
        maintenance = db.query(func.count(Hardware.id)).filter(Hardware.status == HardwareStatus.MAINTENANCE).scalar()
        error = db.query(func.count(Hardware.id)).filter(Hardware.status == HardwareStatus.ERROR).scalar()
        
        return {
            "total_hardware": total,
            "active_hardware": active,
            "offline_hardware": offline,
            "maintenance_hardware": maintenance,
            "error_hardware": error,
            "by_status": {status.value: count for status, count in status_counts},
            "by_type": {hw_type.value: count for hw_type, count in type_counts},
            "by_location": {location_id: count for location_id, count in location_counts if location_id}
        }


hardware = CRUDHardware(Hardware) 