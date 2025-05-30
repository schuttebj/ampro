from typing import List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.crud.base import CRUDBase
from app.models.printer import Printer, PrinterStatus, PrinterType
from app.schemas.printer import PrinterCreate, PrinterUpdate


class CRUDPrinter(CRUDBase[Printer, PrinterCreate, PrinterUpdate]):
    
    def get_by_code(self, db: Session, *, code: str) -> Optional[Printer]:
        """Get printer by code"""
        return db.query(Printer).filter(Printer.code == code).first()
    
    def get_by_location(self, db: Session, *, location_id: int) -> List[Printer]:
        """Get all printers at a specific location"""
        return db.query(Printer).filter(
            and_(
                Printer.location_id == location_id,
                Printer.is_active == True
            )
        ).all()
    
    def get_active_printers(self, db: Session) -> List[Printer]:
        """Get all active printers"""
        return db.query(Printer).filter(
            and_(
                Printer.is_active == True,
                Printer.status.in_([PrinterStatus.ACTIVE, PrinterStatus.MAINTENANCE])
            )
        ).all()
    
    def get_by_status(self, db: Session, *, status: PrinterStatus) -> List[Printer]:
        """Get printers by status"""
        return db.query(Printer).filter(
            and_(
                Printer.status == status,
                Printer.is_active == True
            )
        ).all()
    
    def get_by_type(self, db: Session, *, printer_type: PrinterType) -> List[Printer]:
        """Get printers by type"""
        return db.query(Printer).filter(
            and_(
                Printer.printer_type == printer_type,
                Printer.is_active == True
            )
        ).all()
    
    def search_printers(
        self, 
        db: Session, 
        *, 
        location_id: Optional[int] = None,
        status: Optional[PrinterStatus] = None,
        printer_type: Optional[PrinterType] = None,
        search_term: Optional[str] = None
    ) -> List[Printer]:
        """Search printers with multiple filters"""
        query = db.query(Printer).filter(Printer.is_active == True)
        
        if location_id:
            query = query.filter(Printer.location_id == location_id)
        
        if status:
            query = query.filter(Printer.status == status)
            
        if printer_type:
            query = query.filter(Printer.printer_type == printer_type)
            
        if search_term:
            query = query.filter(
                or_(
                    Printer.name.ilike(f"%{search_term}%"),
                    Printer.code.ilike(f"%{search_term}%"),
                    Printer.model.ilike(f"%{search_term}%"),
                    Printer.manufacturer.ilike(f"%{search_term}%")
                )
            )
        
        return query.order_by(Printer.name).all()
    
    def update_status(
        self, 
        db: Session, 
        *, 
        printer_id: int, 
        status: PrinterStatus,
        notes: Optional[str] = None
    ) -> Optional[Printer]:
        """Update printer status"""
        printer = self.get(db, id=printer_id)
        if printer:
            update_data = {"status": status}
            if notes:
                update_data["notes"] = notes
            return self.update(db, db_obj=printer, obj_in=update_data)
        return None
    
    def assign_to_location(
        self, 
        db: Session, 
        *, 
        printer_id: int, 
        location_id: int
    ) -> Optional[Printer]:
        """Assign printer to a location"""
        printer = self.get(db, id=printer_id)
        if printer:
            return self.update(db, db_obj=printer, obj_in={"location_id": location_id})
        return None


printer = CRUDPrinter(Printer) 