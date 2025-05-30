from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from app.crud.base import CRUDBase
from app.models.license import PrintJob, PrintJobStatus, ShippingRecord, ShippingStatus
from app.schemas.print_job import PrintJobCreate, PrintJobUpdate, ShippingRecordCreate, ShippingRecordUpdate


class CRUDPrintJob(CRUDBase[PrintJob, PrintJobCreate, PrintJobUpdate]):
    def get_by_application_id(self, db: Session, *, application_id: int) -> List[PrintJob]:
        """Get all print jobs for an application."""
        return db.query(PrintJob).filter(PrintJob.application_id == application_id).all()
    
    def get_by_license_id(self, db: Session, *, license_id: int) -> List[PrintJob]:
        """Get all print jobs for a license."""
        return db.query(PrintJob).filter(PrintJob.license_id == license_id).all()
    
    def get_queue(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[PrintJob]:
        """Get print jobs in queue ordered by priority and queue time."""
        return (
            db.query(PrintJob)
            .filter(PrintJob.status.in_([PrintJobStatus.QUEUED, PrintJobStatus.ASSIGNED]))
            .order_by(PrintJob.priority.desc(), PrintJob.queued_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_status(self, db: Session, *, status: PrintJobStatus, skip: int = 0, limit: int = 100) -> List[PrintJob]:
        """Get print jobs by status."""
        return (
            db.query(PrintJob)
            .filter(PrintJob.status == status)
            .order_by(PrintJob.queued_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_assigned_to_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[PrintJob]:
        """Get print jobs assigned to a specific user."""
        return (
            db.query(PrintJob)
            .filter(
                and_(
                    PrintJob.assigned_to_user_id == user_id,
                    PrintJob.status.in_([PrintJobStatus.ASSIGNED, PrintJobStatus.PRINTING])
                )
            )
            .order_by(PrintJob.assigned_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def assign_to_user(self, db: Session, *, print_job_id: int, user_id: int) -> Optional[PrintJob]:
        """Assign a print job to a user."""
        print_job = self.get(db, id=print_job_id)
        if print_job and print_job.status == PrintJobStatus.QUEUED:
            from datetime import datetime
            update_data = {
                "assigned_to_user_id": user_id,
                "assigned_at": datetime.utcnow(),
                "status": PrintJobStatus.ASSIGNED
            }
            return self.update(db, db_obj=print_job, obj_in=update_data)
        return None
    
    def start_printing(self, db: Session, *, print_job_id: int, user_id: int, printer_name: str = None) -> Optional[PrintJob]:
        """Mark a print job as started."""
        print_job = self.get(db, id=print_job_id)
        if print_job and print_job.status == PrintJobStatus.ASSIGNED:
            from datetime import datetime
            update_data = {
                "status": PrintJobStatus.PRINTING,
                "started_at": datetime.utcnow(),
                "printer_name": printer_name
            }
            return self.update(db, db_obj=print_job, obj_in=update_data)
        return None
    
    def complete_printing(self, db: Session, *, print_job_id: int, user_id: int, copies_printed: int = 1, notes: str = None) -> Optional[PrintJob]:
        """Mark a print job as completed."""
        print_job = self.get(db, id=print_job_id)
        if print_job and print_job.status == PrintJobStatus.PRINTING:
            from datetime import datetime
            update_data = {
                "status": PrintJobStatus.COMPLETED,
                "completed_at": datetime.utcnow(),
                "printed_by_user_id": user_id,
                "copies_printed": copies_printed,
                "print_notes": notes
            }
            return self.update(db, db_obj=print_job, obj_in=update_data)
        return None
    
    def get_statistics(self, db: Session) -> dict:
        """Get print job statistics."""
        stats = {}
        
        # Count records for each status
        for status in PrintJobStatus:
            count = db.query(func.count(PrintJob.id)).filter(PrintJob.status == status).scalar()
            stats[status.value.lower()] = count or 0  # Return lowercase keys for API compatibility
        
        return stats

    def get_by_assigned_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[PrintJob]:
        """Get print jobs assigned to a specific user."""
        return (
            db.query(PrintJob)
            .filter(
                and_(
                    PrintJob.assigned_to_user_id == user_id,
                    PrintJob.status.in_([PrintJobStatus.ASSIGNED, PrintJobStatus.PRINTING])
                )
            )
            .order_by(PrintJob.assigned_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_printer_queue(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[PrintJob]:
        """Get print queue for a specific printer operator."""
        return (
            db.query(PrintJob)
            .filter(
                or_(
                    and_(PrintJob.status == PrintJobStatus.QUEUED, PrintJob.assigned_to_user_id.is_(None)),
                    PrintJob.assigned_to_user_id == user_id
                )
            )
            .order_by(PrintJob.priority.desc(), PrintJob.queued_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def count_printer_queue(self, db: Session, *, user_id: int) -> int:
        """Count print jobs for a specific printer operator."""
        return db.query(PrintJob).filter(
            or_(
                and_(PrintJob.status == PrintJobStatus.QUEUED, PrintJob.assigned_to_user_id.is_(None)),
                PrintJob.assigned_to_user_id == user_id
            )
        ).count()
    
    def get_queue_statistics(self, db: Session) -> dict:
        """Get queue statistics."""
        stats = {}
        
        # Count records for each status
        for status in PrintJobStatus:
            count = db.query(func.count(PrintJob.id)).filter(PrintJob.status == status).scalar()
            stats[status.value.lower()] = count or 0  # Return lowercase keys for API compatibility
        
        return stats

    def get_user_statistics(self, db: Session, *, user_id: int) -> dict:
        """Get statistics for a specific user."""
        completed_count = db.query(func.count(PrintJob.id)).filter(
            and_(
                PrintJob.printed_by_user_id == user_id,
                PrintJob.status == PrintJobStatus.COMPLETED
            )
        ).scalar() or 0
        
        assigned_count = db.query(func.count(PrintJob.id)).filter(
            PrintJob.assigned_to_user_id == user_id
        ).scalar() or 0
        
        return {
            "completed": completed_count,
            "assigned": assigned_count
        }


class CRUDShippingRecord(CRUDBase[ShippingRecord, ShippingRecordCreate, ShippingRecordUpdate]):
    def get_by_application_id(self, db: Session, *, application_id: int) -> Optional[ShippingRecord]:
        """Get shipping record for an application."""
        return db.query(ShippingRecord).filter(ShippingRecord.application_id == application_id).first()
    
    def get_by_tracking_number(self, db: Session, *, tracking_number: str) -> Optional[ShippingRecord]:
        """Get shipping record by tracking number."""
        return db.query(ShippingRecord).filter(ShippingRecord.tracking_number == tracking_number).first()
    
    def get_by_status(self, db: Session, *, status: ShippingStatus, skip: int = 0, limit: int = 100) -> List[ShippingRecord]:
        """Get shipping records by status."""
        return (
            db.query(ShippingRecord)
            .filter(ShippingRecord.status == status)
            .order_by(ShippingRecord.shipped_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_collection_point(self, db: Session, *, collection_point: str, skip: int = 0, limit: int = 100) -> List[ShippingRecord]:
        """Get shipping records for a collection point."""
        return (
            db.query(ShippingRecord)
            .filter(ShippingRecord.collection_point == collection_point)
            .order_by(ShippingRecord.shipped_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def ship_record(self, db: Session, *, shipping_id: int, user_id: int, tracking_number: str = None, shipping_method: str = None) -> Optional[ShippingRecord]:
        """Mark a shipping record as shipped."""
        shipping_record = self.get(db, id=shipping_id)
        if shipping_record and shipping_record.status == ShippingStatus.PENDING:
            from datetime import datetime
            update_data = {
                "status": ShippingStatus.IN_TRANSIT,
                "shipped_at": datetime.utcnow(),
                "shipped_by_user_id": user_id,
                "tracking_number": tracking_number,
                "shipping_method": shipping_method
            }
            return self.update(db, db_obj=shipping_record, obj_in=update_data)
        return None
    
    def deliver_record(self, db: Session, *, shipping_id: int, user_id: int, notes: str = None) -> Optional[ShippingRecord]:
        """Mark a shipping record as delivered."""
        shipping_record = self.get(db, id=shipping_id)
        if shipping_record and shipping_record.status == ShippingStatus.IN_TRANSIT:
            from datetime import datetime
            update_data = {
                "status": ShippingStatus.DELIVERED,
                "delivered_at": datetime.utcnow(),
                "received_by_user_id": user_id,
                "shipping_notes": notes
            }
            return self.update(db, db_obj=shipping_record, obj_in=update_data)
        return None
    
    def get_statistics(self, db: Session) -> dict:
        """Get shipping statistics."""
        stats = {}
        
        # Use raw SQL to avoid enum casting issues
        # This handles cases where database has different case than enum expects
        try:
            # Get counts using raw text matching to be more flexible
            result = db.execute(text("""
                SELECT status, COUNT(*) as count 
                FROM shippingrecord 
                GROUP BY status
            """))
            
            # Initialize all statuses to 0
            stats = {
                "pending": 0,
                "in_transit": 0,
                "delivered": 0,
                "failed": 0
            }
            
            # Update with actual counts, normalizing case
            for row in result:
                status_lower = row.status.lower()
                if status_lower in stats:
                    stats[status_lower] = row.count
                elif status_lower == "in_transit":
                    stats["in_transit"] = row.count
                else:
                    # Handle any unexpected values
                    print(f"Warning: Unexpected shipping status '{row.status}' found in database")
                    
        except Exception as e:
            print(f"Error getting shipping statistics: {e}")
            # Return default stats on error
            stats = {
                "pending": 0,
                "in_transit": 0,
                "delivered": 0,
                "failed": 0
            }
        
        return stats


print_job = CRUDPrintJob(PrintJob)
shipping_record = CRUDShippingRecord(ShippingRecord) 