from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class PrintingType(str, enum.Enum):
    LOCAL = "LOCAL"          # Location has its own printers
    CENTRALIZED = "CENTRALIZED"  # Print jobs sent to another location
    HYBRID = "HYBRID"        # Some jobs local, some centralized
    DISABLED = "DISABLED"    # No printing capabilities


class Location(BaseModel):
    """
    Location model for managing collection points where licenses are processed and collected.
    """
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), default="South Africa", nullable=False)
    
    # Contact information
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    manager_name = Column(String(100), nullable=True)
    
    # Operational details
    operating_hours = Column(Text, nullable=True)  # JSON string with hours
    services_offered = Column(Text, nullable=True)  # JSON string with services
    capacity_per_day = Column(Integer, default=50, nullable=False)  # Max applications per day
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    accepts_applications = Column(Boolean, default=True, nullable=False)
    accepts_collections = Column(Boolean, default=True, nullable=False)
    
    # Printing Configuration
    printing_enabled = Column(Boolean, default=True, nullable=False)
    printing_type = Column(Enum(PrintingType), default=PrintingType.LOCAL, nullable=False)
    default_print_destination_id = Column(Integer, ForeignKey("location.id"), nullable=True)
    auto_assign_print_jobs = Column(Boolean, default=True, nullable=False)
    max_print_jobs_per_user = Column(Integer, default=10, nullable=False)
    print_job_priority_default = Column(Integer, default=1, nullable=False)
    
    # Special notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="location")
    user_locations = relationship("UserLocation", back_populates="location", cascade="all, delete-orphan")
    applications = relationship("LicenseApplication", back_populates="location")
    printers = relationship("Printer", back_populates="location")
    hardware_devices = relationship("Hardware", back_populates="location")
    
    # Self-referential relationship for default print destination
    default_print_destination = relationship("Location", remote_side="Location.id")
    
    # Print jobs originating from and targeting this location
    source_print_jobs = relationship("PrintJob", foreign_keys="PrintJob.source_location_id", back_populates="source_location")
    target_print_jobs = relationship("PrintJob", foreign_keys="PrintJob.target_location_id", back_populates="target_location")
    
    def __repr__(self):
        return f"<Location {self.code}: {self.name}>"
    
    @property
    def full_address(self):
        """Get formatted full address"""
        address_parts = [self.address_line1]
        if self.address_line2:
            address_parts.append(self.address_line2)
        address_parts.extend([self.city, self.state_province, self.postal_code])
        if self.country != "South Africa":
            address_parts.append(self.country)
        return ", ".join(address_parts)
    
    @property
    def active_printers(self):
        """Get all active printers at this location"""
        return [p for p in self.printers if p.is_active and p.status in ['active', 'maintenance']]
    
    @property
    def print_users(self):
        """Get all users who can print at this location"""
        from app.models.user import UserRole
        return [ul.user for ul in self.user_locations if ul.can_print and ul.user.role == UserRole.PRINTER] 