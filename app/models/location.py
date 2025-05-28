from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


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
    
    # Special notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="location")
    applications = relationship("LicenseApplication", back_populates="location")
    
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