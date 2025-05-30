from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.user_location import UserLocation
from app.models.user import User, UserRole
from app.models.location import Location
from app.schemas.user_location import UserLocationCreate, UserLocationUpdate


class CRUDUserLocation(CRUDBase[UserLocation, UserLocationCreate, UserLocationUpdate]):
    
    def get_user_locations(self, db: Session, *, user_id: int) -> List[UserLocation]:
        """Get all locations for a specific user"""
        return db.query(UserLocation).filter(UserLocation.user_id == user_id).all()
    
    def get_location_users(self, db: Session, *, location_id: int) -> List[UserLocation]:
        """Get all users at a specific location"""
        return db.query(UserLocation).filter(UserLocation.location_id == location_id).all()
    
    def get_print_users_for_location(self, db: Session, *, location_id: int) -> List[UserLocation]:
        """Get all users who can print at a specific location"""
        return db.query(UserLocation).filter(
            and_(
                UserLocation.location_id == location_id,
                UserLocation.can_print == True
            )
        ).all()
    
    def get_users_by_role_and_location(
        self, 
        db: Session, 
        *, 
        location_id: int, 
        role: UserRole
    ) -> List[User]:
        """Get users with specific role at a location"""
        return db.query(User).join(UserLocation).filter(
            and_(
                UserLocation.location_id == location_id,
                User.role == role
            )
        ).all()
    
    def assign_user_to_location(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        location_id: int,
        is_primary: bool = False,
        can_print: bool = False
    ) -> UserLocation:
        """Assign a user to a location"""
        
        # If setting as primary, unset other primary locations for this user
        if is_primary:
            db.query(UserLocation).filter(
                and_(
                    UserLocation.user_id == user_id,
                    UserLocation.is_primary == True
                )
            ).update({"is_primary": False})
        
        # Check if assignment already exists
        existing = db.query(UserLocation).filter(
            and_(
                UserLocation.user_id == user_id,
                UserLocation.location_id == location_id
            )
        ).first()
        
        if existing:
            # Update existing assignment
            update_data = {
                "is_primary": is_primary,
                "can_print": can_print
            }
            return self.update(db, db_obj=existing, obj_in=update_data)
        else:
            # Create new assignment
            obj_in = UserLocationCreate(
                user_id=user_id,
                location_id=location_id,
                is_primary=is_primary,
                can_print=can_print
            )
            return self.create(db, obj_in=obj_in)
    
    def remove_user_from_location(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        location_id: int
    ) -> bool:
        """Remove user from location"""
        result = db.query(UserLocation).filter(
            and_(
                UserLocation.user_id == user_id,
                UserLocation.location_id == location_id
            )
        ).delete()
        db.commit()
        return result > 0
    
    def set_primary_location(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        location_id: int
    ) -> Optional[UserLocation]:
        """Set a location as primary for a user"""
        
        # First, unset all primary locations for this user
        db.query(UserLocation).filter(
            and_(
                UserLocation.user_id == user_id,
                UserLocation.is_primary == True
            )
        ).update({"is_primary": False})
        
        # Set the new primary location
        user_location = db.query(UserLocation).filter(
            and_(
                UserLocation.user_id == user_id,
                UserLocation.location_id == location_id
            )
        ).first()
        
        if user_location:
            return self.update(db, db_obj=user_location, obj_in={"is_primary": True})
        
        return None
    
    def update_print_permission(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        location_id: int,
        can_print: bool
    ) -> Optional[UserLocation]:
        """Update print permission for user at location"""
        user_location = db.query(UserLocation).filter(
            and_(
                UserLocation.user_id == user_id,
                UserLocation.location_id == location_id
            )
        ).first()
        
        if user_location:
            return self.update(db, db_obj=user_location, obj_in={"can_print": can_print})
        
        return None
    
    def get_user_primary_location(self, db: Session, *, user_id: int) -> Optional[UserLocation]:
        """Get user's primary location"""
        return db.query(UserLocation).filter(
            and_(
                UserLocation.user_id == user_id,
                UserLocation.is_primary == True
            )
        ).first()
    
    def bulk_assign_users_to_location(
        self, 
        db: Session, 
        *, 
        user_ids: List[int], 
        location_id: int,
        can_print: bool = False
    ) -> List[UserLocation]:
        """Assign multiple users to a location"""
        assignments = []
        for user_id in user_ids:
            assignment = self.assign_user_to_location(
                db, 
                user_id=user_id, 
                location_id=location_id, 
                can_print=can_print
            )
            assignments.append(assignment)
        return assignments


user_location = CRUDUserLocation(UserLocation) 