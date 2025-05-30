from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User, UserRole
from app.models.user_location import UserLocation
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    CRUD operations for User model.
    """
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        """
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        Get a user by username.
        """
        return db.query(User).filter(User.username == username).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password.
        """
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
            is_active=obj_in.is_active,
            role=obj_in.role,
            department=obj_in.department,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update a user, hashing the password if it's provided.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password.
        """
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """
        Check if user is active.
        """
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """
        Check if user is superuser.
        """
        return user.is_superuser
    
    # NEW: Location and Printer Management Methods
    
    def get_by_role(self, db: Session, *, role: UserRole) -> List[User]:
        """Get all users with a specific role"""
        return db.query(User).filter(
            and_(
                User.role == role,
                User.is_active == True
            )
        ).all()
    
    def get_printer_users(self, db: Session) -> List[User]:
        """Get all users with PRINTER role"""
        return self.get_by_role(db, role=UserRole.PRINTER)
    
    def get_printer_users_for_location(self, db: Session, *, location_id: int) -> List[User]:
        """Get all printer users who can print at a specific location"""
        return db.query(User).join(UserLocation).filter(
            and_(
                User.role == UserRole.PRINTER,
                User.is_active == True,
                UserLocation.location_id == location_id,
                UserLocation.can_print == True
            )
        ).all()
    
    def get_users_by_location(self, db: Session, *, location_id: int) -> List[User]:
        """Get all users assigned to a specific location"""
        return db.query(User).join(UserLocation).filter(
            and_(
                UserLocation.location_id == location_id,
                User.is_active == True
            )
        ).all()
    
    def search_users(
        self, 
        db: Session, 
        *, 
        role: Optional[UserRole] = None,
        location_id: Optional[int] = None,
        search_term: Optional[str] = None,
        can_print: Optional[bool] = None
    ) -> List[User]:
        """Search users with multiple filters"""
        query = db.query(User).filter(User.is_active == True)
        
        if role:
            query = query.filter(User.role == role)
        
        if location_id:
            query = query.join(UserLocation).filter(UserLocation.location_id == location_id)
            if can_print is not None:
                query = query.filter(UserLocation.can_print == can_print)
        
        if search_term:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search_term}%"),
                    User.email.ilike(f"%{search_term}%"),
                    User.full_name.ilike(f"%{search_term}%"),
                    User.department.ilike(f"%{search_term}%")
                )
            )
        
        return query.order_by(User.full_name).all()


user = CRUDUser(User) 