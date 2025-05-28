from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def get_by_code(self, db: Session, *, code: str) -> Optional[Location]:
        """Get location by code"""
        return db.query(Location).filter(Location.code == code).first()
    
    def get_active_locations(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Location]:
        """Get all active locations"""
        return (
            db.query(self.model)
            .filter(Location.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_locations_accepting_applications(self, db: Session) -> List[Location]:
        """Get locations that accept new applications"""
        return (
            db.query(self.model)
            .filter(
                Location.is_active == True,
                Location.accepts_applications == True
            )
            .all()
        )
    
    def get_locations_accepting_collections(self, db: Session) -> List[Location]:
        """Get locations that accept license collections"""
        return (
            db.query(self.model)
            .filter(
                Location.is_active == True,
                Location.accepts_collections == True
            )
            .all()
        )
    
    def create_with_code(
        self, db: Session, *, obj_in: LocationCreate
    ) -> Location:
        """Create location ensuring unique code"""
        # Generate code if not provided
        if not obj_in.code:
            obj_in.code = self.generate_location_code(obj_in.name)
        
        return self.create(db, obj_in=obj_in)
    
    def generate_location_code(self, name: str) -> str:
        """Generate a unique location code from name"""
        # Simple implementation - take first 3 letters of each word, uppercase
        words = name.split()
        code_parts = []
        for word in words[:3]:  # Max 3 words
            code_parts.append(word[:3].upper())
        
        base_code = "".join(code_parts)
        return base_code[:8]  # Max 8 characters
    
    def update_status(
        self,
        db: Session,
        *,
        db_obj: Location,
        is_active: bool,
        accepts_applications: Optional[bool] = None,
        accepts_collections: Optional[bool] = None
    ) -> Location:
        """Update location status"""
        update_data = {"is_active": is_active}
        if accepts_applications is not None:
            update_data["accepts_applications"] = accepts_applications
        if accepts_collections is not None:
            update_data["accepts_collections"] = accepts_collections
            
        return self.update(db, db_obj=db_obj, obj_in=update_data)


location = CRUDLocation(Location) 