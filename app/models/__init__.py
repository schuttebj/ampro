# Import all models to ensure they are registered with SQLAlchemy
# This prevents relationship resolution errors

from .base import BaseModel
from .user import User, UserRole
from .citizen import Citizen, Gender, MaritalStatus, IdentificationType, OfficialLanguage, AddressType
from .location import Location, PrintingType
from .printer import Printer, PrinterType, PrinterStatus
from .hardware import Hardware, HardwareType, HardwareStatus
from .user_location import UserLocation
from .license import (
    License, 
    LicenseCategory, 
    LicenseStatus, 
    LicenseApplication,
    ApplicationStatus,
    ApplicationType,
    TransactionType as LicenseTransactionType,
    CardNoticeStatus,
    PaymentMethod,
    PaymentStatus,
    LicenseFee,
    Payment,
    PrintJob,
    PrintJobStatus,
    ShippingRecord,
    ShippingStatus
)
from .audit import AuditLog, ActionType, ResourceType, Transaction, TransactionType, TransactionStatus

# Ensure all models are available when this package is imported
__all__ = [
    "BaseModel",
    "User", 
    "UserRole",
    "Citizen",
    "Gender",
    "MaritalStatus",
    "IdentificationType",
    "OfficialLanguage",
    "AddressType",
    "Location",
    "PrintingType",
    "Printer",
    "PrinterType", 
    "PrinterStatus",
    "Hardware",
    "HardwareType",
    "HardwareStatus",
    "UserLocation",
    "License",
    "LicenseCategory",
    "LicenseStatus",
    "LicenseApplication",
    "ApplicationStatus", 
    "ApplicationType",
    "LicenseTransactionType",
    "CardNoticeStatus",
    "PaymentMethod",
    "PaymentStatus",
    "LicenseFee",
    "Payment",
    "PrintJob",
    "PrintJobStatus",
    "ShippingRecord",
    "ShippingStatus",
    "AuditLog",
    "ActionType",
    "ResourceType", 
    "Transaction",
    "TransactionType",
    "TransactionStatus"
] 