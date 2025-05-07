from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.license import LicenseCategory, LicenseStatus, ApplicationStatus


class LicenseBase(BaseModel):
    """
    Base schema for license with common attributes.
    """
    license_number: Optional[str] = None
    citizen_id: Optional[int] = None
    category: Optional[LicenseCategory] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[LicenseStatus] = None
    restrictions: Optional[str] = None
    medical_conditions: Optional[str] = None
    file_url: Optional[str] = None
    barcode_data: Optional[str] = None


class LicenseCreate(LicenseBase):
    """
    Schema for creating a new license.
    """
    license_number: str
    citizen_id: int
    category: LicenseCategory
    issue_date: date = Field(default_factory=lambda: date.today())
    expiry_date: date = Field(default_factory=lambda: date.today().replace(year=date.today().year + 5))
    status: LicenseStatus = LicenseStatus.ACTIVE


class LicenseUpdate(LicenseBase):
    """
    Schema for updating an existing license.
    """
    pass


class LicenseInDBBase(LicenseBase):
    """
    Base schema for license in DB with ID.
    """
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class License(LicenseInDBBase):
    """
    Schema for returning license information.
    """
    pass


class LicenseWithCitizen(License):
    """
    Schema for returning license with citizen information.
    """
    from app.schemas.citizen import Citizen
    citizen: Citizen


# Application schemas
class LicenseApplicationBase(BaseModel):
    """
    Base schema for license application with common attributes.
    """
    citizen_id: Optional[int] = None
    applied_category: Optional[LicenseCategory] = None
    status: Optional[ApplicationStatus] = None
    application_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_date: Optional[datetime] = None
    review_notes: Optional[str] = None
    documents_verified: Optional[bool] = False
    medical_verified: Optional[bool] = False
    payment_verified: Optional[bool] = False
    approved_license_id: Optional[int] = None


class LicenseApplicationCreate(LicenseApplicationBase):
    """
    Schema for creating a new license application.
    """
    citizen_id: int
    applied_category: LicenseCategory
    status: ApplicationStatus = ApplicationStatus.SUBMITTED


class LicenseApplicationUpdate(LicenseApplicationBase):
    """
    Schema for updating an existing license application.
    """
    pass


class LicenseApplicationInDBBase(LicenseApplicationBase):
    """
    Base schema for license application in DB with ID.
    """
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class LicenseApplication(LicenseApplicationInDBBase):
    """
    Schema for returning license application information.
    """
    pass


class LicenseApplicationDetail(LicenseApplication):
    """
    Schema for returning detailed license application information.
    """
    from app.schemas.citizen import Citizen
    from app.schemas.user import User
    
    citizen: Optional[Citizen] = None
    reviewer: Optional[User] = None
    license: Optional[License] = None 