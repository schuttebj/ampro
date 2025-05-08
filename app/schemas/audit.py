from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel

from app.models.audit import ActionType, ResourceType, TransactionType, TransactionStatus

# Avoid circular imports
if TYPE_CHECKING:
    from app.schemas.user import User
    from app.schemas.citizen import Citizen
    from app.schemas.license import License, LicenseApplication


class AuditLogBase(BaseModel):
    """
    Base schema for audit log with common attributes.
    """
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action_type: Optional[ActionType] = None
    resource_type: Optional[ResourceType] = None
    resource_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    description: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    """
    Schema for creating a new audit log entry.
    """
    action_type: ActionType
    resource_type: ResourceType
    timestamp: datetime = datetime.utcnow()


class AuditLogUpdate(AuditLogBase):
    """
    Schema for updating an existing audit log entry.
    """
    pass


class AuditLogInDBBase(AuditLogBase):
    """
    Base schema for audit log in DB with ID.
    """
    id: int

    class Config:
        from_attributes = True


class AuditLog(AuditLogInDBBase):
    """
    Schema for returning audit log information.
    """
    pass


# Transaction schemas
class TransactionBase(BaseModel):
    """
    Base schema for transaction with common attributes.
    """
    transaction_type: Optional[TransactionType] = None
    transaction_ref: Optional[str] = None
    status: Optional[TransactionStatus] = None
    user_id: Optional[int] = None
    citizen_id: Optional[int] = None
    license_id: Optional[int] = None
    application_id: Optional[int] = None
    initiated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    amount: Optional[int] = None
    notes: Optional[str] = None
    transaction_metadata: Optional[Dict[str, Any]] = None


class TransactionCreate(TransactionBase):
    """
    Schema for creating a new transaction.
    """
    transaction_type: TransactionType
    transaction_ref: str
    status: TransactionStatus = TransactionStatus.PENDING
    initiated_at: datetime = datetime.utcnow()


class TransactionUpdate(TransactionBase):
    """
    Schema for updating an existing transaction.
    """
    status: Optional[TransactionStatus] = None
    completed_at: Optional[datetime] = None


class TransactionInDBBase(TransactionBase):
    """
    Base schema for transaction in DB with ID.
    """
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class Transaction(TransactionInDBBase):
    """
    Schema for returning transaction information.
    """
    pass


class TransactionDetail(Transaction):
    """
    Schema for returning detailed transaction information.
    Use simple attributes to avoid circular references
    """
    # Using ID references instead of nested objects to avoid circular references
    user_id: Optional[int] = None
    citizen_id: Optional[int] = None
    license_id: Optional[int] = None
    application_id: Optional[int] = None 