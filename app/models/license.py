from sqlalchemy import Column, String, ForeignKey, Date, Text, Enum, Boolean, DateTime, Integer
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
    PENDING_COLLECTION = "pending_collection"  # License issued but not collected
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class License(BaseModel):
    """
    License model to store driver's license information.
    Enhanced with ISO 18013-1:2018 compliance for African driver's licenses.
    """
    license_number = Column(String, unique=True, index=True, nullable=False)
    citizen_id = Column(Integer, ForeignKey("citizen.id"), nullable=False)
    
    # License details
    category = Column(Enum(LicenseCategory), nullable=False)
    issue_date = Column(Date, default=datetime.utcnow, nullable=False)
    expiry_date = Column(Date, default=lambda: datetime.utcnow() + timedelta(days=5*365), nullable=False)
    status = Column(Enum(LicenseStatus), default=LicenseStatus.PENDING_COLLECTION, nullable=False)
    
    # ISO 18013 Compliance Fields
    iso_country_code = Column(String(3), default="ZAF", nullable=False)  # ISO 3166-1 alpha-3 country code
    iso_issuing_authority = Column(String(100), nullable=False, default="Department of Transport")  # Issuing authority identifier
    iso_document_number = Column(String(50), nullable=True)  # ISO document number (different from license_number)
    iso_version = Column(String(10), default="18013-1:2018", nullable=False)  # ISO standard version
    
    # Biometric and Security Features
    biometric_template = Column(Text, nullable=True)  # Encrypted biometric data
    digital_signature = Column(Text, nullable=True)  # Digital signature for authenticity
    security_features = Column(Text, nullable=True)  # JSON string of security features
    
    # Machine Readable Zone (MRZ) Data
    mrz_line1 = Column(String(44), nullable=True)  # First line of MRZ
    mrz_line2 = Column(String(44), nullable=True)  # Second line of MRZ
    mrz_line3 = Column(String(44), nullable=True)  # Third line of MRZ (if applicable)
    
    # RFID/Chip Data (for smart cards)
    chip_serial_number = Column(String(50), nullable=True)  # RFID chip serial number
    chip_data_encrypted = Column(Text, nullable=True)  # Encrypted chip data
    
    # International Recognition
    international_validity = Column(Boolean, default=True, nullable=False)  # Valid for international use
    vienna_convention_compliant = Column(Boolean, default=True, nullable=False)  # Vienna Convention compliance
    
    # Restrictions and conditions
    restrictions = Column(Text, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    
    # License file information
    file_url = Column(String, nullable=True)
    barcode_data = Column(String, nullable=True)
    
    # Generated license files storage
    front_image_path = Column(String, nullable=True)
    back_image_path = Column(String, nullable=True)
    front_pdf_path = Column(String, nullable=True)
    back_pdf_path = Column(String, nullable=True)
    combined_pdf_path = Column(String, nullable=True)
    watermark_pdf_path = Column(String, nullable=True)  # ISO security watermark
    
    # Image processing tracking
    original_photo_path = Column(String, nullable=True)
    processed_photo_path = Column(String, nullable=True)
    photo_last_updated = Column(DateTime, nullable=True)
    
    # Generation metadata
    last_generated = Column(DateTime, nullable=True)
    generation_version = Column(String, default="1.0", nullable=False)
    
    # Collection tracking
    collection_point = Column(String, nullable=True)  # Where citizen should collect
    collected_at = Column(DateTime, nullable=True)
    collected_by_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    # Relationships
    citizen = relationship("Citizen", back_populates="licenses")
    collected_by = relationship("User", foreign_keys=[collected_by_user_id])
    
    def __repr__(self):
        return f"<License {self.license_number}: {self.category} - {self.status}>"


class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "submitted"                    # Initial application
    UNDER_REVIEW = "under_review"             # Being reviewed by staff
    PENDING_DOCUMENTS = "pending_documents"    # Waiting for additional documents
    PENDING_PAYMENT = "pending_payment"        # Waiting for payment
    APPROVED = "approved"                      # Application approved, ready for license generation
    LICENSE_GENERATED = "license_generated"    # License files created
    QUEUED_FOR_PRINTING = "queued_for_printing"  # In print queue
    PRINTING = "printing"                      # Currently being printed
    PRINTED = "printed"                        # Physical card printed
    SHIPPED = "shipped"                        # Sent to collection point
    READY_FOR_COLLECTION = "ready_for_collection"  # At collection point
    COMPLETED = "completed"                    # Collected by citizen
    REJECTED = "rejected"                      # Application rejected
    CANCELLED = "cancelled"                    # Application cancelled


class PrintJobStatus(str, enum.Enum):
    QUEUED = "queued"                         # Waiting in print queue
    ASSIGNED = "assigned"                     # Assigned to printer operator
    PRINTING = "printing"                     # Currently printing
    COMPLETED = "completed"                   # Successfully printed
    FAILED = "failed"                         # Print job failed
    CANCELLED = "cancelled"                   # Print job cancelled


class ShippingStatus(str, enum.Enum):
    PENDING = "pending"                       # Ready to ship
    IN_TRANSIT = "in_transit"                # Being shipped
    DELIVERED = "delivered"                   # Delivered to collection point
    FAILED = "failed"                         # Shipping failed


class ApplicationType(str, enum.Enum):
    NEW = "new"                               # First-time application
    RENEWAL = "renewal"                       # License renewal
    REPLACEMENT = "replacement"               # Lost/damaged license replacement
    UPGRADE = "upgrade"                       # Category upgrade (e.g., B to C)
    CONVERSION = "conversion"                 # Foreign license conversion


class LicenseApplication(BaseModel):
    """
    License application model to track license applications.
    """
    citizen_id = Column(Integer, ForeignKey("citizen.id"), nullable=False)
    applied_category = Column(Enum(LicenseCategory), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.SUBMITTED, nullable=False)
    application_type = Column(Enum(ApplicationType), default=ApplicationType.NEW, nullable=False)
    
    # Application details
    application_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # For renewals/replacements, reference the previous license
    previous_license_id = Column(Integer, ForeignKey("license.id"), nullable=True)
    
    # Location assignment - where application is processed and collection point
    location_id = Column(Integer, ForeignKey("location.id"), nullable=True)
    
    # Review information
    reviewed_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    review_date = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Document verification
    documents_verified = Column(Boolean, default=False, nullable=False)
    medical_verified = Column(Boolean, default=False, nullable=False)
    payment_verified = Column(Boolean, default=False, nullable=False)
    payment_amount = Column(Integer, nullable=True)  # Amount in cents
    payment_reference = Column(String, nullable=True)
    
    # Collection details
    collection_point = Column(String, nullable=True)  # Deprecated - use location_id instead
    preferred_collection_date = Column(Date, nullable=True)
    
    # When approved, create license
    approved_license_id = Column(Integer, ForeignKey("license.id"), nullable=True)
    
    # Relationships
    citizen = relationship("Citizen")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    license = relationship("License")
    location = relationship("Location", back_populates="applications")
    print_jobs = relationship("PrintJob", back_populates="application")
    shipping_record = relationship("ShippingRecord", back_populates="application", uselist=False)
    
    def __repr__(self):
        return f"<LicenseApplication {self.id}: {self.applied_category} - {self.status}>"


class PrintJob(BaseModel):
    """
    Model to track print jobs for license cards.
    """
    application_id = Column(Integer, ForeignKey("licenseapplication.id"), nullable=False)
    license_id = Column(Integer, ForeignKey("license.id"), nullable=False)
    
    # Print job details
    status = Column(Enum(PrintJobStatus), default=PrintJobStatus.QUEUED, nullable=False)
    priority = Column(Integer, default=1, nullable=False)  # 1=normal, 2=high, 3=urgent
    
    # File paths for printing
    front_pdf_path = Column(String, nullable=False)
    back_pdf_path = Column(String, nullable=False)
    combined_pdf_path = Column(String, nullable=True)
    
    # Print tracking
    queued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Staff assignment
    assigned_to_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    printed_by_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    # Print details
    printer_name = Column(String, nullable=True)
    copies_printed = Column(Integer, default=1, nullable=False)
    print_notes = Column(Text, nullable=True)
    
    # Relationships
    application = relationship("LicenseApplication", back_populates="print_jobs")
    license = relationship("License")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    printed_by = relationship("User", foreign_keys=[printed_by_user_id])
    
    def __repr__(self):
        return f"<PrintJob {self.id}: App {self.application_id} - {self.status}>"


class ShippingRecord(BaseModel):
    """
    Model to track shipping of printed license cards to collection points.
    """
    application_id = Column(Integer, ForeignKey("licenseapplication.id"), nullable=False)
    license_id = Column(Integer, ForeignKey("license.id"), nullable=False)
    print_job_id = Column(Integer, ForeignKey("printjob.id"), nullable=False)
    
    # Shipping details
    status = Column(Enum(ShippingStatus), default=ShippingStatus.PENDING, nullable=False)
    tracking_number = Column(String, nullable=True)
    
    # Addresses
    collection_point = Column(String, nullable=False)
    collection_address = Column(Text, nullable=True)
    
    # Shipping timeline
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Staff tracking
    shipped_by_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    received_by_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    # Additional details
    shipping_method = Column(String, nullable=True)  # courier, internal, etc.
    shipping_notes = Column(Text, nullable=True)
    
    # Relationships
    application = relationship("LicenseApplication", back_populates="shipping_record")
    license = relationship("License")
    print_job = relationship("PrintJob")
    shipped_by = relationship("User", foreign_keys=[shipped_by_user_id])
    received_by = relationship("User", foreign_keys=[received_by_user_id])
    
    def __repr__(self):
        return f"<ShippingRecord {self.id}: App {self.application_id} - {self.status}>" 