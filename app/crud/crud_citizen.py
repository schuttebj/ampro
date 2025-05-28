from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.citizen import Citizen
from app.schemas.citizen import CitizenCreate, CitizenUpdate


class CRUDCitizen(CRUDBase[Citizen, CitizenCreate, CitizenUpdate]):
    """
    CRUD operations for Citizen model.
    """
    def get_by_id_number(self, db: Session, *, id_number: str) -> Optional[Citizen]:
        """
        Get a citizen by ID number.
        """
        return db.query(Citizen).filter(Citizen.id_number == id_number).first()

    def search_by_name(
        self, db: Session, *, first_name: str = None, last_name: str = None, 
        skip: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> List[Citizen]:
        """
        Search citizens by first name and/or last name. By default only searches active citizens.
        """
        query = db.query(Citizen)
        
        # Filter by active status unless explicitly including inactive
        if not include_inactive:
            query = query.filter(Citizen.is_active == True)
            
        if first_name:
            query = query.filter(Citizen.first_name.ilike(f"%{first_name}%"))
        if last_name:
            query = query.filter(Citizen.last_name.ilike(f"%{last_name}%"))
        return query.offset(skip).limit(limit).all()
    
    def get_with_licenses(self, db: Session, *, id: int) -> Optional[Citizen]:
        """
        Get a citizen with their licenses.
        """
        return db.query(Citizen).filter(Citizen.id == id).first()
    
    def update_photo_paths(self, db: Session, *, citizen_id: int, 
                          stored_photo_path: str = None, 
                          processed_photo_path: str = None) -> Optional[Citizen]:
        """
        Update citizen photo paths after processing
        
        Args:
            db: Database session
            citizen_id: Citizen ID
            stored_photo_path: Path to stored original photo
            processed_photo_path: Path to processed ISO-compliant photo
        
        Returns:
            Updated citizen object
        """
        citizen_obj = self.get(db, id=citizen_id)
        if not citizen_obj:
            return None
        
        update_data = {}
        
        if stored_photo_path:
            update_data["stored_photo_path"] = stored_photo_path
            update_data["photo_uploaded_at"] = datetime.now()
            
        if processed_photo_path:
            update_data["processed_photo_path"] = processed_photo_path
            update_data["photo_processed_at"] = datetime.now()
        
        return self.update(db, db_obj=citizen_obj, obj_in=update_data)
    
    def get_citizens_without_processed_photos(self, db: Session, *, 
                                            skip: int = 0, 
                                            limit: int = 100) -> List[Citizen]:
        """
        Get citizens who have photo URLs but no processed photos
        
        Args:
            db: Database session
            skip: Records to skip
            limit: Maximum records to return
        
        Returns:
            List of citizens needing photo processing
        """
        return (db.query(Citizen)
                .filter(Citizen.photo_url.isnot(None))
                .filter(Citizen.processed_photo_path.is_(None))
                .offset(skip)
                .limit(limit)
                .all())
    
    def get_citizens_with_outdated_photos(self, db: Session, *, 
                                        hours_threshold: int = 24,
                                        skip: int = 0, 
                                        limit: int = 100) -> List[Citizen]:
        """
        Get citizens whose photos might be outdated based on upload/processing time
        
        Args:
            db: Database session
            hours_threshold: Hours after which photo is considered outdated
            skip: Records to skip
            limit: Maximum records to return
        
        Returns:
            List of citizens with potentially outdated photos
        """
        cutoff_time = datetime.now() - datetime.timedelta(hours=hours_threshold)
        
        return (db.query(Citizen)
                .filter(
                    (Citizen.photo_uploaded_at < cutoff_time) |
                    (Citizen.photo_processed_at < cutoff_time)
                )
                .offset(skip)
                .limit(limit)
                .all())
    
    def clear_photo_data(self, db: Session, *, citizen_id: int) -> Optional[Citizen]:
        """
        Clear photo data for a citizen (useful when removing photos)
        
        Args:
            db: Database session
            citizen_id: Citizen ID
        
        Returns:
            Updated citizen object
        """
        citizen_obj = self.get(db, id=citizen_id)
        if not citizen_obj:
            return None
        
        update_data = {
            "stored_photo_path": None,
            "processed_photo_path": None,
            "photo_uploaded_at": None,
            "photo_processed_at": None
        }
        
        return self.update(db, db_obj=citizen_obj, obj_in=update_data)

    def get_active_citizens(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Citizen]:
        """
        Get all active citizens (is_active = True)
        """
        return (
            db.query(self.model)
            .filter(Citizen.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )


citizen = CRUDCitizen(Citizen) 