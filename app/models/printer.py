from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import BaseModel


class PrinterType(str, enum.Enum):
    CARD_PRINTER = "CARD_PRINTER"
    DOCUMENT_PRINTER = "DOCUMENT_PRINTER"
    PHOTO_PRINTER = "PHOTO_PRINTER"
    THERMAL_PRINTER = "THERMAL_PRINTER"
    INKJET_PRINTER = "INKJET_PRINTER"
    LASER_PRINTER = "LASER_PRINTER"


class PrinterStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"


class Printer(BaseModel):
    __tablename__ = "printer"

    name = Column(String(100), nullable=False, index=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    printer_type = Column(Enum(PrinterType), nullable=False)
    model = Column(String(100), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    status = Column(Enum(PrinterStatus), default=PrinterStatus.ACTIVE, nullable=False, index=True)
    capabilities = Column(JSON, nullable=True)  # e.g., {"double_sided": true, "color": false, "max_paper_size": "A4"}
    settings = Column(JSON, nullable=True)  # e.g., {"default_paper_size": "A4", "quality": "high"}
    location_id = Column(Integer, ForeignKey("location.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    last_maintenance = Column(DateTime, nullable=True)
    next_maintenance = Column(DateTime, nullable=True)

    # Relationships
    location = relationship("Location", back_populates="printers")
    print_jobs = relationship("PrintJob", back_populates="printer") 