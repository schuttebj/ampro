from typing import Optional, List, TYPE_CHECKING
from datetime import date
from pydantic import BaseModel, EmailStr, Field

from app.models.citizen import Gender, MaritalStatus

# Avoid circular imports
if TYPE_CHECKING:
    from app.schemas.license import License


class CitizenBase(BaseModel):
    """
    Base schema for citizen with common attributes.
    """
    id_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    
    # Contact information
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    
    # Address information
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "South Africa"
    
    # Additional information
    birth_place: Optional[str] = None
    nationality: Optional[str] = None
    photo_url: Optional[str] = None


class CitizenCreate(CitizenBase):
    """
    Schema for creating a new citizen.
    """
    id_number: str = Field(..., min_length=13, max_length=13)
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender


class CitizenUpdate(CitizenBase):
    """
    Schema for updating an existing citizen.
    """
    pass


class CitizenInDBBase(CitizenBase):
    """
    Base schema for citizen in DB with ID.
    """
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class Citizen(CitizenInDBBase):
    """
    Schema for returning citizen information.
    """
    pass


class CitizenDetail(Citizen):
    """
    Schema for returning detailed citizen information including licenses.
    """
    licenses: List["License"] = [] 