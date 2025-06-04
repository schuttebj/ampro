from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.models.base import BaseModel


class ActionType(str, enum.Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PRINT = "PRINT"
    EXPORT = "EXPORT"
    VERIFY = "VERIFY"
    GENERATE = "GENERATE"


class ResourceType(str, enum.Enum):
    USER = "USER"
    CITIZEN = "CITIZEN"
    LICENSE = "LICENSE"
    APPLICATION = "APPLICATION"
    LOCATION = "LOCATION"
    FILE = "FILE"
    SYSTEM = "SYSTEM"
    PAYMENT = "PAYMENT"
    FEE = "FEE"


class AuditLog(BaseModel):
    """
    Model for tracking all system actions for security and auditing purposes.
    """
    # Who performed the action
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # What action was performed
    action_type = Column(Enum(ActionType), nullable=False)
    resource_type = Column(Enum(ResourceType), nullable=False)
    resource_id = Column(String, nullable=True)
    
    # When the action was performed
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Details of the action
    description = Column(Text, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action_type} on {self.resource_type}>"


class TransactionType(str, enum.Enum):
    LICENSE_ISSUANCE = "license_issuance"
    LICENSE_RENEWAL = "license_renewal"
    LICENSE_REPLACEMENT = "license_replacement"
    APPLICATION_SUBMISSION = "application_submission"
    APPLICATION_APPROVAL = "application_approval"
    APPLICATION_REJECTION = "application_rejection"
    FEE_PAYMENT = "fee_payment"
    DOCUMENT_UPLOAD = "document_upload"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transaction(BaseModel):
    """
    Model for tracking system transactions.
    """
    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False)
    transaction_ref = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    
    # Who initiated the transaction
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    citizen_id = Column(Integer, ForeignKey("citizen.id"), nullable=True)
    
    # Related resources
    license_id = Column(Integer, ForeignKey("license.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("licenseapplication.id"), nullable=True)
    
    # Transaction timing
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Additional details
    amount = Column(Integer, nullable=True)  # Amount in cents if payment
    notes = Column(Text, nullable=True)
    transaction_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User")
    citizen = relationship("Citizen")
    license = relationship("License")
    application = relationship("LicenseApplication")
    
    def __repr__(self):
        return f"<Transaction {self.transaction_ref}: {self.transaction_type} - {self.status}>" 