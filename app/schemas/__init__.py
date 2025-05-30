# Import all schemas to make them available when importing from app.schemas

from .user import User, UserCreate, UserUpdate, UserInDB
from .citizen import Citizen, CitizenCreate, CitizenUpdate, CitizenInDB
from .license import License, LicenseCreate, LicenseUpdate, LicenseInDBBase, LicenseApplication, LicenseApplicationCreate, LicenseApplicationUpdate, LicenseApplicationInDBBase
from .location import Location, LocationCreate, LocationUpdate, LocationInDBBase
from .print_job import (
    PrintJob, PrintJobCreate, PrintJobUpdate, PrintJobInDB,
    PrintQueue, PrintJobStatistics, ShippingRecord, ShippingRecordCreate,
    ShippingRecordUpdate, ShippingStatistics, WorkflowStatus
)
from .audit import AuditLog, AuditLogCreate, AuditLogUpdate, AuditLogInDBBase
from .token import Token, TokenPayload
from .printer import Printer, PrinterCreate, PrinterUpdate, PrinterInDB
from .user_location import UserLocation, UserLocationCreate, UserLocationUpdate, UserLocationInDB

__all__ = [
    # User schemas
    "User", "UserCreate", "UserUpdate", "UserInDB",
    # Citizen schemas
    "Citizen", "CitizenCreate", "CitizenUpdate", "CitizenInDB",
    # License schemas
    "License", "LicenseCreate", "LicenseUpdate", "LicenseInDBBase",
    "LicenseApplication", "LicenseApplicationCreate", "LicenseApplicationUpdate", "LicenseApplicationInDBBase",
    # Location schemas
    "Location", "LocationCreate", "LocationUpdate", "LocationInDBBase",
    # Print job schemas
    "PrintJob", "PrintJobCreate", "PrintJobUpdate", "PrintJobInDB",
    "PrintQueue", "PrintJobStatistics", "ShippingRecord", "ShippingRecordCreate",
    "ShippingRecordUpdate", "ShippingStatistics", "WorkflowStatus",
    # Audit schemas
    "AuditLog", "AuditLogCreate", "AuditLogUpdate", "AuditLogInDBBase",
    # Token schemas
    "Token", "TokenPayload",
    # Printer schemas
    "Printer", "PrinterCreate", "PrinterUpdate", "PrinterInDB",
    # User location schemas
    "UserLocation", "UserLocationCreate", "UserLocationUpdate", "UserLocationInDB",
] 