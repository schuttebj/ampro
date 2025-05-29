from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

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
            .filter(PrintJob.status.in_(['QUEUED', 'ASSIGNED']))
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
                    PrintJob.status.in_(['ASSIGNED', 'PRINTING'])
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
        if print_job and print_job.status.value == 'QUEUED':
            from datetime import datetime
            update_data = {
                "assigned_to_user_id": user_id,
                "assigned_at": datetime.utcnow(),
                "status": 'ASSIGNED'
            }
            return self.update(db, db_obj=print_job, obj_in=update_data)
        return None
    
    def start_printing(self, db: Session, *, print_job_id: int, user_id: int, printer_name: str = None) -> Optional[PrintJob]:
        """Mark a print job as started."""
        print_job = self.get(db, id=print_job_id)
        if print_job and print_job.status.value == 'ASSIGNED':
            from datetime import datetime
            update_data = {
                "status": 'PRINTING',
                "started_at": datetime.utcnow(),
                "printer_name": printer_name
            }
            return self.update(db, db_obj=print_job, obj_in=update_data)
        return None
    
    def complete_printing(self, db: Session, *, print_job_id: int, user_id: int, copies_printed: int = 1, notes: str = None) -> Optional[PrintJob]:
        """Mark a print job as completed."""
        print_job = self.get(db, id=print_job_id)
        if print_job and print_job.status.value == 'PRINTING':
            from datetime import datetime
            update_data = {
                "status": 'COMPLETED',
                "completed_at": datetime.utcnow(),
                "printed_by_user_id": user_id,
                "copies_printed": copies_printed,
                "print_notes": notes
            }
            return self.update(db, db_obj=print_job, obj_in=update_data)
        return None
    
    def get_statistics(self, db: Session) -> dict:
        """Get print job statistics."""
        from sqlalchemy import func
        
        stats = {}
        for status in PrintJobStatus:
            count = db.query(func.count(PrintJob.id)).filter(PrintJob.status == status.value).scalar()
            stats[status.value] = count
        
        return stats


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
        if shipping_record and shipping_record.status == ShippingStatus.PENDING.value:
            from datetime import datetime
            update_data = {
                "status": ShippingStatus.IN_TRANSIT.value,
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
        if shipping_record and shipping_record.status == ShippingStatus.IN_TRANSIT.value:
            from datetime import datetime
            update_data = {
                "status": ShippingStatus.DELIVERED.value,
                "delivered_at": datetime.utcnow(),
                "received_by_user_id": user_id,
                "shipping_notes": notes
            }
            return self.update(db, db_obj=shipping_record, obj_in=update_data)
        return None
    
    def get_statistics(self, db: Session) -> dict:
        """Get shipping statistics."""
        from sqlalchemy import func
        
        stats = {}
        for status in ShippingStatus:
            count = db.query(func.count(ShippingRecord.id)).filter(ShippingRecord.status == status.value).scalar()
            stats[status.value] = count
        
        return stats


print_job = CRUDPrintJob(PrintJob)
shipping_record = CRUDShippingRecord(ShippingRecord) 