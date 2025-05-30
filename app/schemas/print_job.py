from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel

from app.models.license import PrintJobStatus, ShippingStatus


# Print Job Schemas
class PrintJobBase(BaseModel):
    priority: Optional[int] = 1
    front_pdf_path: str
    back_pdf_path: str
    combined_pdf_path: Optional[str] = None
    printer_name: Optional[str] = None
    copies_printed: Optional[int] = 1
    print_notes: Optional[str] = None


class PrintJobCreate(PrintJobBase):
    application_id: int
    license_id: int
    status: Optional[str] = "QUEUED"


class PrintJobUpdate(BaseModel):
    status: Optional[PrintJobStatus] = None
    priority: Optional[int] = None
    assigned_to_user_id: Optional[int] = None
    printed_by_user_id: Optional[int] = None
    printer_name: Optional[str] = None
    copies_printed: Optional[int] = None
    print_notes: Optional[str] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PrintJobInDBBase(PrintJobBase):
    id: int
    application_id: int
    license_id: int
    status: PrintJobStatus
    queued_at: datetime
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_to_user_id: Optional[int] = None
    printed_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class PrintJob(PrintJobInDBBase):
    pass


class PrintJobInDB(PrintJobInDBBase):
    pass


# Print Job Assignment Schema
class PrintJobAssignment(BaseModel):
    print_job_id: int
    user_id: int


class PrintJobStart(BaseModel):
    print_job_id: int
    user_id: int
    printer_name: Optional[str] = None


class PrintJobComplete(BaseModel):
    print_job_id: int
    user_id: int
    copies_printed: Optional[int] = 1
    notes: Optional[str] = None


# Shipping Record Schemas
class ShippingRecordBase(BaseModel):
    collection_point: str
    collection_address: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_notes: Optional[str] = None
    tracking_number: Optional[str] = None


class ShippingRecordCreate(ShippingRecordBase):
    application_id: int
    license_id: int
    print_job_id: int


class ShippingRecordUpdate(BaseModel):
    status: Optional[ShippingStatus] = None
    tracking_number: Optional[str] = None
    collection_point: Optional[str] = None
    collection_address: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_notes: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    shipped_by_user_id: Optional[int] = None
    received_by_user_id: Optional[int] = None


class ShippingRecordInDBBase(ShippingRecordBase):
    id: int
    application_id: int
    license_id: int
    print_job_id: int
    status: ShippingStatus
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    shipped_by_user_id: Optional[int] = None
    received_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ShippingRecord(ShippingRecordInDBBase):
    pass


class ShippingRecordInDB(ShippingRecordInDBBase):
    pass


# Shipping Action Schemas
class ShippingAction(BaseModel):
    shipping_id: int
    user_id: int
    tracking_number: Optional[str] = None
    shipping_method: Optional[str] = None
    notes: Optional[str] = None


# Statistics Schemas
class PrintJobStatistics(BaseModel):
    queued: int
    assigned: int
    printing: int
    completed: int
    failed: int
    cancelled: int
    total: int


class ShippingStatistics(BaseModel):
    pending: int
    in_transit: int
    delivered: int
    failed: int
    total: int


# Combined Workflow Schemas
class WorkflowStatus(BaseModel):
    application_id: int
    application_status: str
    license_id: Optional[int] = None
    license_status: Optional[str] = None
    print_job_id: Optional[int] = None
    print_job_status: Optional[str] = None
    shipping_id: Optional[int] = None
    shipping_status: Optional[str] = None
    collection_point: Optional[str] = None
    last_updated: datetime


class PrintQueue(BaseModel):
    print_jobs: List[PrintJob]
    total_count: int
    queued_count: int
    assigned_count: int


class CollectionPointSummary(BaseModel):
    collection_point: str
    pending_shipments: int
    in_transit_shipments: int
    ready_for_collection: int
    total_licenses: int 