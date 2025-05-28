from sqlalchemy import Column, String, Date, ForeignKey, Text, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.models.base import BaseModel


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class MaritalStatus(str, enum.Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


class Citizen(BaseModel):
    """
    Citizen model to store citizen information from government databases.
    """
    id_number = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    marital_status = Column(Enum(MaritalStatus), nullable=True)
    
    # Contact information
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    # Address information
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state_province = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, default="South Africa", nullable=True)
    
    # Additional information
    birth_place = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    
    # Photo management - enhanced for production use
    photo_url = Column(String, nullable=True)  # External URL (original)
    stored_photo_path = Column(String, nullable=True)  # Local stored copy
    processed_photo_path = Column(String, nullable=True)  # ISO-compliant processed version
    photo_uploaded_at = Column(DateTime, nullable=True)
    photo_processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    licenses = relationship("License", back_populates="citizen")
    
    def __repr__(self):
        return f"<Citizen {self.id_number}: {self.first_name} {self.last_name}>" 