from typing import Optional, List, TYPE_CHECKING, Any, Union, Dict, ForwardRef
from datetime import date, datetime
from pydantic import BaseModel, Field, validator

from app.models.license import LicenseCategory, LicenseStatus, ApplicationStatus, ApplicationType, TransactionType, CardNoticeStatus, PaymentMethod, PaymentStatus

# Avoid circular imports
if TYPE_CHECKING:
    from app.schemas.citizen import Citizen
    from app.schemas.user import User

# Forward reference to avoid circular imports
Citizen = ForwardRef("Citizen")


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


# =============================================================================
# LICENSE FEE SCHEMAS
# =============================================================================

class LicenseFeeBase(BaseModel):
    """Base schema for license fees."""
    license_category: LicenseCategory
    transaction_type: TransactionType
    application_type: ApplicationType
    base_fee: int = Field(..., description="Base fee in cents")
    processing_fee: int = Field(0, description="Processing fee in cents")
    delivery_fee: int = Field(0, description="Delivery fee in cents")
    minimum_age: Optional[int] = None
    maximum_age: Optional[int] = None
    is_active: bool = True
    effective_date: date = Field(default_factory=date.today)
    description: Optional[str] = None
    notes: Optional[str] = None


class LicenseFeeCreate(LicenseFeeBase):
    """Schema for creating a license fee."""
    pass


class LicenseFeeUpdate(LicenseFeeBase):
    """Schema for updating a license fee."""
    license_category: Optional[LicenseCategory] = None
    transaction_type: Optional[TransactionType] = None
    application_type: Optional[ApplicationType] = None
    base_fee: Optional[int] = None


class LicenseFee(LicenseFeeBase):
    """Schema for returning license fee information."""
    id: int
    created_at: datetime
    updated_at: datetime
    total_fee: int = Field(..., description="Total fee including all components")
    
    class Config:
        from_attributes = True


# =============================================================================
# PAYMENT SCHEMAS
# =============================================================================

class PaymentBase(BaseModel):
    """Base schema for payments."""
    amount: int = Field(..., description="Payment amount in cents")
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    external_reference: Optional[str] = None
    payment_notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Schema for creating a payment."""
    application_id: int


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    external_reference: Optional[str] = None
    payment_notes: Optional[str] = None
    payment_date: Optional[datetime] = None


class Payment(PaymentBase):
    """Schema for returning payment information."""
    id: int
    application_id: int
    status: PaymentStatus
    payment_date: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    processed_by_user_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# LICENSE APPLICATION SCHEMAS
# =============================================================================

class LicenseApplicationBase(BaseModel):
    """Base schema for license applications with all Section A-D fields."""
    applied_category: LicenseCategory
    application_type: ApplicationType = ApplicationType.NEW
    transaction_type: TransactionType = TransactionType.DRIVING_LICENCE
    
    # Section A: Applicant Details (additional fields)
    photograph_attached: bool = False
    photograph_count: int = 0
    
    # Section B: Class of Motor Vehicle & Previous License History
    previous_license_refusal: bool = False
    refusal_details: Optional[str] = None
    
    # Section C: Notice of Card Status
    card_notice_status: Optional[CardNoticeStatus] = None
    police_report_station: Optional[str] = None
    police_report_cas_number: Optional[str] = None
    office_of_issue: Optional[str] = None
    card_status_change_date: Optional[date] = None
    
    # Section D: Declaration by Applicant
    not_disqualified: bool = False
    not_suspended: bool = False
    not_cancelled: bool = False
    
    # Medical declarations
    no_uncontrolled_epilepsy: bool = False
    no_sudden_fainting: bool = False
    no_mental_illness: bool = False
    no_muscular_incoordination: bool = False
    no_uncontrolled_diabetes: bool = False
    no_defective_vision: bool = False
    no_unsafe_disability: bool = False
    no_narcotic_addiction: bool = False
    no_alcohol_addiction: bool = False
    medically_fit: bool = False
    
    # Declaration completion
    information_true_correct: bool = False
    applicant_signature_date: Optional[date] = None
    
    # Additional fields
    previous_license_id: Optional[int] = None
    location_id: Optional[int] = None
    preferred_collection_date: Optional[date] = None
    review_notes: Optional[str] = None


class LicenseApplicationCreate(LicenseApplicationBase):
    """Schema for creating a license application."""
    citizen_id: int


class LicenseApplicationUpdate(LicenseApplicationBase):
    """Schema for updating a license application."""
    citizen_id: Optional[int] = None
    applied_category: Optional[LicenseCategory] = None
    status: Optional[ApplicationStatus] = None
    documents_verified: Optional[bool] = None
    medical_verified: Optional[bool] = None
    payment_verified: Optional[bool] = None
    payment_amount: Optional[int] = None
    payment_reference: Optional[str] = None
    is_draft: Optional[bool] = None


class LicenseApplicationSubmit(BaseModel):
    """Schema for submitting a draft application."""
    submit: bool = True


class LicenseApplication(LicenseApplicationBase):
    """Schema for returning license application information."""
    id: int
    citizen_id: int
    status: ApplicationStatus
    application_date: datetime
    last_updated: datetime
    
    # Review information
    reviewed_by: Optional[int] = None
    review_date: Optional[datetime] = None
    
    # Verification status
    documents_verified: bool = False
    medical_verified: bool = False
    payment_verified: bool = False
    payment_amount: Optional[int] = None
    payment_reference: Optional[str] = None
    
    # Draft management
    is_draft: bool = True
    submitted_at: Optional[datetime] = None
    
    # References
    approved_license_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# No need to import and resolve forward refs as we're using dictionaries at the API level
# This avoids circular import issues