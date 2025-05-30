from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.models.printer import PrinterType, PrinterStatus


class PrinterBase(BaseModel):
    name: str
    code: str
    printer_type: PrinterType
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None
    status: PrinterStatus = PrinterStatus.ACTIVE
    capabilities: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    location_id: Optional[int] = None
    notes: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None


class PrinterCreate(PrinterBase):
    pass


class PrinterUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    printer_type: Optional[PrinterType] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[PrinterStatus] = None
    capabilities: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    location_id: Optional[int] = None
    notes: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    is_active: Optional[bool] = None


class PrinterInDBBase(PrinterBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True


class Printer(PrinterInDBBase):
    pass


class PrinterInDB(PrinterInDBBase):
    pass 