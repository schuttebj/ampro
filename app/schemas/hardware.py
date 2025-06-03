from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.hardware import HardwareType, HardwareStatus


class HardwareBase(BaseModel):
    """Base schema for hardware with common attributes."""
    name: Optional[str] = None
    code: Optional[str] = None
    hardware_type: Optional[HardwareType] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None
    usb_port: Optional[str] = None
    device_id: Optional[str] = None
    status: Optional[HardwareStatus] = None
    capabilities: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    driver_info: Optional[Dict[str, Any]] = None
    location_id: Optional[int] = None
    notes: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None


class HardwareCreate(HardwareBase):
    """Schema for creating new hardware."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    hardware_type: HardwareType
    status: HardwareStatus = HardwareStatus.ACTIVE


class HardwareUpdate(HardwareBase):
    """Schema for updating hardware."""
    pass


class HardwareInDBBase(HardwareBase):
    """Base schema for hardware in database."""
    id: int
    last_online: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Hardware(HardwareInDBBase):
    """Schema for returning hardware information."""
    pass


class HardwareInDB(HardwareInDBBase):
    """Schema for hardware stored in database."""
    pass


class HardwareWithLocation(Hardware):
    """Schema for hardware with location information."""
    location_name: Optional[str] = None
    location_code: Optional[str] = None


class HardwareStatusUpdate(BaseModel):
    """Schema for updating hardware status."""
    status: HardwareStatus
    notes: Optional[str] = None


class HardwareUsageLog(BaseModel):
    """Schema for hardware usage logging."""
    hardware_id: int
    user_id: int
    action: str  # "capture_photo", "scan_fingerprint", etc.
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Additional context data
    timestamp: datetime


class WebcamCaptureRequest(BaseModel):
    """Schema for webcam photo capture request."""
    hardware_id: int
    citizen_id: int
    quality: Optional[str] = "high"  # high, medium, low
    format: Optional[str] = "jpeg"  # jpeg, png
    metadata: Optional[Dict[str, Any]] = None


class WebcamCaptureResponse(BaseModel):
    """Schema for webcam photo capture response."""
    success: bool
    photo_url: Optional[str] = None
    stored_photo_path: Optional[str] = None
    processed_photo_path: Optional[str] = None
    error_message: Optional[str] = None
    hardware_id: int
    citizen_id: int
    captured_at: datetime


class HardwareStatistics(BaseModel):
    """Schema for hardware statistics."""
    total_hardware: int
    active_hardware: int
    offline_hardware: int
    maintenance_hardware: int
    error_hardware: int
    by_type: Dict[str, int]
    by_location: Dict[str, int]
    recent_usage: List[HardwareUsageLog] 