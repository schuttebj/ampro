from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Base schema for user with common attributes.
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    department: Optional[str] = None


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    """
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserUpdate(UserBase):
    """
    Schema for updating an existing user.
    """
    password: Optional[str] = Field(None, min_length=8)


class UserInDBBase(UserBase):
    """
    Base schema for user in DB with ID.
    """
    id: int

    class Config:
        from_attributes = True


class User(UserInDBBase):
    """
    Schema for returning user information.
    """
    pass


class UserInDB(UserInDBBase):
    """
    Schema for user in DB with hashed password.
    """
    hashed_password: str 