from typing import Optional, List, TYPE_CHECKING, Any, Union, Dict, ForwardRef
from datetime import date, datetime
from pydantic import BaseModel, Field, validator

from app.models.license import LicenseCategory, LicenseStatus, ApplicationStatus, ApplicationType

# Avoid circular imports
if TYPE_CHECKING:
    from app.schemas.citizen import Citizen
    from app.schemas.user import User


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


# Instead of using forward references, we'll handle serialization at the API level
class LicenseWithCitizen(License):
    """
    Schema for returning license with citizen information.
    """
    pass  # Citizen will be handled at the API level with jsonable_encoder


# Application schemas
class LicenseApplicationBase(BaseModel):
    """
    Base schema for license application with common attributes.
    """
    citizen_id: int
    applied_category: LicenseCategory
    status: Optional[ApplicationStatus] = None
    application_type: Optional[ApplicationType] = ApplicationType.NEW
    previous_license_id: Optional[int] = None
    location_id: Optional[int] = None
    application_date: Optional[datetime] = None
    documents_verified: Optional[bool] = False
    medical_verified: Optional[bool] = False
    payment_verified: Optional[bool] = False
    payment_amount: Optional[int] = None
    payment_reference: Optional[str] = None
    collection_point: Optional[str] = None
    preferred_collection_date: Optional[date] = None
    review_notes: Optional[str] = None


class LicenseApplicationCreate(LicenseApplicationBase):
    """
    Schema for creating a new license application.
    """
    citizen_id: int
    applied_category: LicenseCategory
    status: ApplicationStatus = ApplicationStatus.SUBMITTED
    application_type: ApplicationType = ApplicationType.NEW


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
    pass  # Citizen, reviewer, and license will be handled at the API level with jsonable_encoder


# No need to import and resolve forward refs as we're using dictionaries at the API level
# This avoids circular import issues