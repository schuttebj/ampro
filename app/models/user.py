from sqlalchemy import Boolean, Column, String, Enum
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """
    User roles for role-based access control.
    """
    ADMIN = "admin"           # Full system access (equivalent to is_superuser=True)
    MANAGER = "manager"       # Department management, user oversight
    OFFICER = "officer"       # License processing, application review
    PRINTER = "printer"       # Print job processing only
    VIEWER = "viewer"         # Read-only access


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