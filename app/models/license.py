from sqlalchemy import Column, String, ForeignKey, Date, Text, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timedelta

from app.models.base import BaseModel


class LicenseCategory(str, enum.Enum):
    A = "A"     # Motorcycles
    B = "B"     # Light motor vehicles
    C = "C"     # Heavy motor vehicles
    D = "D"     # Combination vehicles
    EB = "EB"   # Light articulated vehicles
    EC = "EC"   # Heavy articulated vehicles


class LicenseStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


class License(BaseModel):
    """
    License model to store driver's license information.
    """
    license_number = Column(String, unique=True, index=True, nullable=False)
    citizen_id = Column(Integer, ForeignKey("citizen.id"), nullable=False)
    
    # License details
    category = Column(Enum(LicenseCategory), nullable=False)
    issue_date = Column(Date, default=datetime.utcnow, nullable=False)
    expiry_date = Column(Date, default=lambda: datetime.utcnow() + timedelta(days=5*365), nullable=False)
    status = Column(Enum(LicenseStatus), default=LicenseStatus.ACTIVE, nullable=False)
    
    # Restrictions and conditions
    restrictions = Column(Text, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    
    # License file information
    file_url = Column(String, nullable=True)
    barcode_data = Column(String, nullable=True)
    
    # Relationships
    citizen = relationship("Citizen", back_populates="licenses")
    
    def __repr__(self):
        return f"<License {self.license_number}: {self.category} - {self.status}>"


class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_DOCUMENTS = "pending_documents"
    COMPLETED = "completed"


class LicenseApplication(BaseModel):
    """
    License application model to track license applications.
    """
    citizen_id = Column(Integer, ForeignKey("citizen.id"), nullable=False)
    applied_category = Column(Enum(LicenseCategory), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.SUBMITTED, nullable=False)
    
    # Application details
    application_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Review information
    reviewed_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    review_date = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Document verification
    documents_verified = Column(Boolean, default=False, nullable=False)
    medical_verified = Column(Boolean, default=False, nullable=False)
    payment_verified = Column(Boolean, default=False, nullable=False)
    
    # When approved, create license
    approved_license_id = Column(Integer, ForeignKey("license.id"), nullable=True)
    
    # Relationships
    citizen = relationship("Citizen")
    reviewer = relationship("User")
    license = relationship("License")
    
    def __repr__(self):
        return f"<LicenseApplication {self.id}: {self.applied_category} - {self.status}>" 