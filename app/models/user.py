from sqlalchemy import Boolean, Column, String, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """
    User roles for role-based access control.
    """
    ADMIN = "ADMIN"           # Full system access (equivalent to is_superuser=True)
    MANAGER = "MANAGER"       # Department management, user oversight
    OFFICER = "OFFICER"       # License processing, application review
    PRINTER = "PRINTER"       # Print job processing only
    VIEWER = "VIEWER"         # Read-only access


class User(BaseModel):
    """
    User model for authentication and authorization.
    """
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False)  # Keep for backward compatibility
    role = Column(Enum(UserRole), default=UserRole.OFFICER, nullable=False)
    department = Column(String, nullable=True)
    
    # Location assignment - clerks are assigned to specific locations
    location_id = Column(Integer, ForeignKey("location.id"), nullable=True)
    
    # Relationships
    location = relationship("Location", back_populates="users")
    user_locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}: {self.role}>"
    
    @property
    def is_admin(self):
        """Check if user has admin privileges"""
        return self.is_superuser or self.role == UserRole.ADMIN
    
    @property
    def can_manage_locations(self):
        """Check if user can manage locations"""
        return self.is_admin or self.role == UserRole.MANAGER
    
    @property
    def assigned_locations(self):
        """Get all locations this user is assigned to"""
        return [ul.location for ul in self.user_locations]
    
    @property
    def can_print_locations(self):
        """Get all locations where this user can print"""
        return [ul.location for ul in self.user_locations if ul.can_print]
    
    @property
    def primary_location(self):
        """Get user's primary location"""
        primary_ul = next((ul for ul in self.user_locations if ul.is_primary), None)
        return primary_ul.location if primary_ul else self.location 