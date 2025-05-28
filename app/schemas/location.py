from typing import Optional
from pydantic import BaseModel


class LocationBase(BaseModel):
    """Base schema for location with common attributes."""
    name: str
    code: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: str
    postal_code: str
    country: str = "South Africa"
    phone_number: Optional[str] = None
    email: Optional[str] = None
    manager_name: Optional[str] = None
    operating_hours: Optional[str] = None
    services_offered: Optional[str] = None
    capacity_per_day: int = 50
    is_active: bool = True
    accepts_applications: bool = True
    accepts_collections: bool = True
    notes: Optional[str] = None


class LocationCreate(LocationBase):
    """Schema for creating a new location."""
    name: str
    address_line1: str
    city: str
    state_province: str
    postal_code: str


class LocationUpdate(LocationBase):
    """Schema for updating an existing location."""
    name: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None


class LocationInDBBase(LocationBase):
    """Base schema for location in DB with ID."""
    id: int
    code: str
    
    class Config:
        from_attributes = True


class Location(LocationInDBBase):
    """Schema for returning location information."""
    pass


class LocationSummary(BaseModel):
    """Schema for location summary in dropdowns."""
    id: int
    name: str
    code: str
    city: str
    is_active: bool
    accepts_applications: bool
    accepts_collections: bool
    
    class Config:
        from_attributes = True 