from typing import Optional, List, TYPE_CHECKING, ForwardRef
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field

from app.models.citizen import Gender, MaritalStatus, IdentificationType, OfficialLanguage, AddressType

# Avoid circular imports
if TYPE_CHECKING:
    from app.schemas.license import License


class CitizenBase(BaseModel):
    """
    Base schema for citizen with common attributes.
    Enhanced with Section A fields from SA driving license application.
    """
    # Basic identification
    id_number: Optional[str] = None
    identification_type: Optional[IdentificationType] = IdentificationType.RSA_ID
    country_of_issue: Optional[str] = None
    nationality: Optional[str] = "South African"
    
    # Names
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    initials: Optional[str] = Field(None, max_length=10)
    
    # Personal details
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    
    # Language preference
    official_language: Optional[OfficialLanguage] = None
    
    # Contact information (extended for SA form requirements)
    email: Optional[EmailStr] = None
    phone_home: Optional[str] = None
    phone_daytime: Optional[str] = None
    phone_cell: Optional[str] = None
    fax_number: Optional[str] = None
    
    # Postal Address
    postal_suburb: Optional[str] = None
    postal_city: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Street Address
    street_address: Optional[str] = None
    street_suburb: Optional[str] = None
    street_city: Optional[str] = None
    street_postal_code: Optional[str] = None
    
    # Address for service of notices
    preferred_address_type: Optional[AddressType] = AddressType.POSTAL
    
    # Legacy fields (keeping for compatibility)
    phone_number: Optional[str] = None  # Deprecated - use phone_cell
    address_line1: Optional[str] = None  # Deprecated - use street_address
    address_line2: Optional[str] = None  # Deprecated
    city: Optional[str] = None  # Deprecated - use postal_city
    state_province: Optional[str] = None
    country: Optional[str] = "South Africa"
    
    # Additional information
    birth_place: Optional[str] = None
    
    # Photo management
    photo_url: Optional[str] = None


class CitizenCreate(CitizenBase):
    """
    Schema for creating a new citizen.
    """
    id_number: str = Field(..., min_length=1, max_length=50)  # Allow various ID formats
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender


class CitizenUpdate(CitizenBase):
    """
    Schema for updating a citizen.
    """
    pass


class CitizenInDBBase(CitizenBase):
    """
    Base schema for citizen in database.
    """
    id: int
    
    # Photo management fields
    stored_photo_path: Optional[str] = None
    processed_photo_path: Optional[str] = None
    photo_uploaded_at: Optional[datetime] = None
    photo_processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Citizen(CitizenInDBBase):
    """
    Schema for returning citizen information.
    """
    pass


class CitizenInDB(CitizenInDBBase):
    """
    Schema for citizen stored in database.
    """
    pass


class CitizenDetail(Citizen):
    """
    Schema for returning detailed citizen information including licenses.
    """
    pass  # Licenses will be handled at the API level with jsonable_encoder

# Update forward references at the end of the module
# This is moved to main.py to avoid circular imports 