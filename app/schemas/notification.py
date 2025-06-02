from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, computed_field

from app.models.notification import NotificationPriority, NotificationType, NotificationCategory, NotificationStatus


# Base schemas
class NotificationBase(BaseModel):
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    category: NotificationCategory
    user_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    auto_dismissible: bool = False
    expires_at: Optional[datetime] = None
    group_id: Optional[str] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    triggered_by_user_id: Optional[int] = None
    audit_log_id: Optional[int] = None
    transaction_id: Optional[int] = None


class NotificationUpdate(BaseModel):
    status: Optional[NotificationStatus] = None
    read_at: Optional[datetime] = None


class NotificationInDB(NotificationBase):
    id: int
    status: NotificationStatus
    triggered_by_user_id: Optional[int] = None
    audit_log_id: Optional[int] = None
    transaction_id: Optional[int] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class Notification(NotificationInDB):
    """Full notification response with computed fields"""
    
    @computed_field
    @property
    def read(self) -> bool:
        return self.status in [NotificationStatus.READ, NotificationStatus.ARCHIVED]
    
    @computed_field
    @property
    def timestamp(self) -> datetime:
        return self.created_at


# Bulk operations
class NotificationBulkUpdate(BaseModel):
    notification_ids: List[int]
    action: str  # 'mark_read', 'archive', 'delete'


class NotificationStats(BaseModel):
    total_notifications: int
    unread_count: int
    critical_count: int
    category_breakdown: Dict[str, int]
    daily_trend: List[Dict[str, Any]]
    response_time_avg: float


# Preference schemas
class NotificationPreferenceBase(BaseModel):
    category_settings: Dict[str, Dict[str, Any]]
    sound_enabled: bool = True
    desktop_notifications: bool = True
    email_notifications: bool = False
    auto_mark_read_delay: int = 30


class NotificationPreferenceCreate(NotificationPreferenceBase):
    user_id: int


class NotificationPreferenceUpdate(BaseModel):
    category_settings: Optional[Dict[str, Dict[str, Any]]] = None
    sound_enabled: Optional[bool] = None
    desktop_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    auto_mark_read_delay: Optional[int] = None


class NotificationPreference(NotificationPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Real-time notification for WebSocket
class NotificationEvent(BaseModel):
    event_type: str  # 'new_notification', 'notification_updated'
    notification: Notification
    user_id: int 