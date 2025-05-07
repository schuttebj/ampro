from typing import List, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.audit import AuditLog, Transaction, ActionType, ResourceType, TransactionType, TransactionStatus
from app.schemas.audit import AuditLogCreate, AuditLogUpdate, TransactionCreate, TransactionUpdate


class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, AuditLogUpdate]):
    """
    CRUD operations for AuditLog model.
    """
    def get_by_user_id(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get all audit logs for a user.
        """
        return db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    def get_by_action_type(self, db: Session, *, action_type: ActionType, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get all audit logs with a specific action type.
        """
        return db.query(AuditLog).filter(AuditLog.action_type == action_type).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    def get_by_resource_type(self, db: Session, *, resource_type: ResourceType, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get all audit logs for a specific resource type.
        """
        return db.query(AuditLog).filter(AuditLog.resource_type == resource_type).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    def get_by_date_range(self, db: Session, *, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get all audit logs within a date range.
        """
        return (db.query(AuditLog)
                .filter(AuditLog.timestamp >= start_date)
                .filter(AuditLog.timestamp <= end_date)
                .order_by(AuditLog.timestamp.desc())
                .offset(skip).limit(limit).all())
    
    def get_by_resource_id(self, db: Session, *, resource_type: ResourceType, resource_id: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get all audit logs for a specific resource.
        """
        return (db.query(AuditLog)
                .filter(AuditLog.resource_type == resource_type)
                .filter(AuditLog.resource_id == resource_id)
                .order_by(AuditLog.timestamp.desc())
                .offset(skip).limit(limit).all())


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    """
    CRUD operations for Transaction model.
    """
    def get_by_transaction_ref(self, db: Session, *, transaction_ref: str) -> Optional[Transaction]:
        """
        Get a transaction by reference.
        """
        return db.query(Transaction).filter(Transaction.transaction_ref == transaction_ref).first()

    def get_by_transaction_type(self, db: Session, *, transaction_type: TransactionType, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """
        Get all transactions of a specific type.
        """
        return db.query(Transaction).filter(Transaction.transaction_type == transaction_type).order_by(Transaction.initiated_at.desc()).offset(skip).limit(limit).all()

    def get_by_status(self, db: Session, *, status: TransactionStatus, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """
        Get all transactions with a specific status.
        """
        return db.query(Transaction).filter(Transaction.status == status).order_by(Transaction.initiated_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_citizen_id(self, db: Session, *, citizen_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """
        Get all transactions for a citizen.
        """
        return db.query(Transaction).filter(Transaction.citizen_id == citizen_id).order_by(Transaction.initiated_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_user_id(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """
        Get all transactions initiated by a user.
        """
        return db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.initiated_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_date_range(self, db: Session, *, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """
        Get all transactions within a date range.
        """
        return (db.query(Transaction)
                .filter(Transaction.initiated_at >= start_date)
                .filter(Transaction.initiated_at <= end_date)
                .order_by(Transaction.initiated_at.desc())
                .offset(skip).limit(limit).all())
    
    def generate_transaction_ref(self) -> str:
        """
        Generate a unique transaction reference.
        """
        # Format: TRN-XXXXXXXX (X = alphanumeric)
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"TRN-{unique_id}"


audit_log = CRUDAuditLog(AuditLog)
transaction = CRUDTransaction(Transaction) 