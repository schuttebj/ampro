from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class NotificationPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"  # Uppercase to match ActionType pattern
    HIGH = "HIGH"          # Uppercase to match ActionType pattern  
    NORMAL = "NORMAL"      # Uppercase to match ActionType pattern
    LOW = "LOW"            # Uppercase to match ActionType pattern


class NotificationType(str, enum.Enum):
    SUCCESS = "SUCCESS"    # Uppercase to match ActionType pattern
    ERROR = "ERROR"        # Uppercase to match ActionType pattern
    WARNING = "WARNING"    # Uppercase to match ActionType pattern
    INFO = "INFO"          # Uppercase to match ActionType pattern


class NotificationCategory(str, enum.Enum):
    APPLICATION = "APPLICATION"        # Uppercase to match ResourceType pattern
    PRINT_JOB = "PRINT_JOB"           # Uppercase to match ResourceType pattern
    SHIPPING = "SHIPPING"             # Uppercase to match ResourceType pattern
    COLLECTION = "COLLECTION"         # Uppercase to match ResourceType pattern
    ISO_COMPLIANCE = "ISO_COMPLIANCE" # Uppercase to match ResourceType pattern
    SYSTEM = "SYSTEM"                 # Uppercase to match ResourceType pattern
    USER_ACTION = "USER_ACTION"       # Uppercase to match ResourceType pattern
    AUTOMATION = "AUTOMATION"         # NEW: For automation features
    BATCH_PROCESSING = "BATCH_PROCESSING"  # NEW: For batch operations
    RULE_ENGINE = "RULE_ENGINE"       # NEW: For rule-based automation
    VALIDATION = "VALIDATION"         # NEW: For validation processes


class NotificationStatus(str, enum.Enum):
    UNREAD = "unread"      # Lowercase to match ApplicationStatus pattern
    READ = "read"          # Lowercase to match ApplicationStatus pattern
    ARCHIVED = "archived"  # Lowercase to match ApplicationStatus pattern
    DISMISSED = "dismissed" # Lowercase to match ApplicationStatus pattern


class Notification(Base):
    """
    Notification model that extends existing audit and transaction functionality
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Core notification data
    title = Column(String(255), nullable=False, index=True)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), nullable=False, default=NotificationType.INFO)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.NORMAL)
    category = Column(Enum(NotificationCategory), nullable=False, index=True)
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.UNREAD)
    
    # Link to existing system entities (leverage existing relationships)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Target user
    triggered_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who triggered it
    audit_log_id = Column(Integer, ForeignKey("audit_logs.id"), nullable=True)  # Link to audit entry
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)  # Link to transaction
    
    # Entity references (flexible linking to any entity)
    entity_type = Column(String(50), nullable=True)  # 'application', 'license', 'citizen', etc.
    entity_id = Column(Integer, nullable=True)
    
    # Notification behavior
    auto_dismissible = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    group_id = Column(String(100), nullable=True, index=True)  # For grouping related notifications
    
    # Action links (for frontend integration)
    action_url = Column(String(255), nullable=True)
    action_label = Column(String(100), nullable=True)
    
    # Additional data (JSON for flexibility)
    metadata = Column(JSON, nullable=True)
    
    # Timestamps (leverage base model pattern)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships (use existing user model)
    target_user = relationship("User", foreign_keys=[user_id], back_populates="notifications_received")
    triggered_by = relationship("User", foreign_keys=[triggered_by_user_id])
    audit_log = relationship("AuditLog", back_populates="notifications")
    transaction = relationship("Transaction", back_populates="notifications")


class NotificationPreference(Base):
    """
    User notification preferences (extends existing user system)
    """
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Category preferences (JSON for flexibility)
    category_settings = Column(JSON, nullable=False, default={
        "APPLICATION": {"enabled": True, "priority_filter": "all", "email": False},
        "PRINT_JOB": {"enabled": True, "priority_filter": "all", "email": False},
        "SHIPPING": {"enabled": True, "priority_filter": "HIGH", "email": True},
        "COLLECTION": {"enabled": True, "priority_filter": "NORMAL", "email": False},
        "ISO_COMPLIANCE": {"enabled": True, "priority_filter": "HIGH", "email": True},
        "SYSTEM": {"enabled": True, "priority_filter": "CRITICAL", "email": True},
        "USER_ACTION": {"enabled": True, "priority_filter": "all", "email": False},
        "AUTOMATION": {"enabled": True, "priority_filter": "HIGH", "email": True},
        "BATCH_PROCESSING": {"enabled": True, "priority_filter": "NORMAL", "email": False},
        "RULE_ENGINE": {"enabled": True, "priority_filter": "HIGH", "email": True},
        "VALIDATION": {"enabled": True, "priority_filter": "HIGH", "email": False}
    })
    
    # General preferences
    sound_enabled = Column(Boolean, default=True)
    desktop_notifications = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=False)
    auto_mark_read_delay = Column(Integer, default=30)  # seconds
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="notification_preferences")