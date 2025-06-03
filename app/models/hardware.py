from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import BaseModel


class HardwareType(str, enum.Enum):
    WEBCAM = "WEBCAM"
    SECURITY_CAMERA = "SECURITY_CAMERA"
    FINGERPRINT_SCANNER = "FINGERPRINT_SCANNER"
    IRIS_SCANNER = "IRIS_SCANNER"
    FACE_RECOGNITION = "FACE_RECOGNITION"
    CARD_READER = "CARD_READER"
    SIGNATURE_PAD = "SIGNATURE_PAD"
    DOCUMENT_SCANNER = "DOCUMENT_SCANNER"
    BARCODE_SCANNER = "BARCODE_SCANNER"
    THERMAL_SENSOR = "THERMAL_SENSOR"
    OTHER = "OTHER"


class HardwareStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"
    CALIBRATING = "CALIBRATING"


class Hardware(BaseModel):
    __tablename__ = "hardware"

    name = Column(String(100), nullable=False, index=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    hardware_type = Column(Enum(HardwareType), nullable=False)
    model = Column(String(100), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    usb_port = Column(String(20), nullable=True)  # For USB-connected devices
    device_id = Column(String(100), nullable=True)  # System device identifier
    status = Column(Enum(HardwareStatus), default=HardwareStatus.ACTIVE, nullable=False, index=True)
    
    # Hardware-specific capabilities and settings
    capabilities = Column(JSON, nullable=True)  # e.g., {"resolution": "1920x1080", "fps": 30, "biometric_types": ["fingerprint", "face"]}
    settings = Column(JSON, nullable=True)  # e.g., {"capture_format": "jpeg", "quality": "high", "timeout": 30}
    driver_info = Column(JSON, nullable=True)  # Driver version, compatibility info
    
    # Location assignment
    location_id = Column(Integer, ForeignKey("location.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Maintenance and monitoring
    notes = Column(Text, nullable=True)
    last_maintenance = Column(DateTime, nullable=True)
    next_maintenance = Column(DateTime, nullable=True)
    last_online = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    last_error_time = Column(DateTime, nullable=True)

    # Relationships
    location = relationship("Location", back_populates="hardware_devices")
    # Future: relationship with hardware usage logs, citizen photo captures, etc.

    def __repr__(self):
        return f"<Hardware {self.code}: {self.name} ({self.hardware_type})>" 