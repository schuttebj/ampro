# Import all models to ensure they are registered with SQLAlchemy
# This prevents relationship resolution errors

from .base import BaseModel
from .user import User, UserRole
from .citizen import Citizen
from .location import Location
from .license import (
    License, 
    LicenseCategory, 
    LicenseStatus, 
    LicenseApplication,
    ApplicationStatus,
    ApplicationType,
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
    "Location", 
    "License",
    "LicenseCategory",
    "LicenseStatus",
    "LicenseApplication",
    "ApplicationStatus", 
    "ApplicationType",
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