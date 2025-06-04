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


class IdentificationType(str, enum.Enum):
    RSA_ID = "rsa_id"                        # RSA ID
    TRAFFIC_REGISTER = "traffic_register"     # Traffic Register Number
    FOREIGN_ID = "foreign_id"                # Foreign ID


class OfficialLanguage(str, enum.Enum):
    AFRIKAANS = "afrikaans"
    NDEBELE = "ndebele"
    NORTHERN_SOTHO = "northern_sotho"
    SOTHO = "sotho"
    SWAZI = "swazi"
    TSONGA = "tsonga"
    TSWANA = "tswana"
    VENDA = "venda"
    XHOSA = "xhosa"
    ZULU = "zulu"


class AddressType(str, enum.Enum):
    POSTAL = "postal"
    STREET = "street"


class Citizen(BaseModel):
    """
    Citizen model to store citizen information from government databases.
    Enhanced with Section A fields from SA driving license application.
    """
    # Basic identification
    id_number = Column(String, unique=True, index=True, nullable=False)
    identification_type = Column(Enum(IdentificationType), default=IdentificationType.RSA_ID, nullable=False)
    country_of_issue = Column(String, nullable=True)  # For foreign IDs
    nationality = Column(String, default="South African", nullable=True)
    
    # Names
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    initials = Column(String(10), nullable=True)  # Max 3 initials
    
    # Personal details
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    marital_status = Column(Enum(MaritalStatus), nullable=True)
    
    # Language preference
    official_language = Column(Enum(OfficialLanguage), nullable=True)
    
    # Contact information (extended for SA form requirements)
    email = Column(String, nullable=True)
    phone_home = Column(String, nullable=True)
    phone_daytime = Column(String, nullable=True)
    phone_cell = Column(String, nullable=True)
    fax_number = Column(String, nullable=True)
    
    # Postal Address
    postal_suburb = Column(String, nullable=True)
    postal_city = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    
    # Street Address
    street_address = Column(String, nullable=True)
    street_suburb = Column(String, nullable=True)
    street_city = Column(String, nullable=True)
    street_postal_code = Column(String, nullable=True)
    
    # Address for service of notices
    preferred_address_type = Column(Enum(AddressType), default=AddressType.POSTAL, nullable=True)
    
    # Legacy fields (keeping for compatibility)
    phone_number = Column(String, nullable=True)  # Deprecated - use phone_cell
    address_line1 = Column(String, nullable=True)  # Deprecated - use street_address
    address_line2 = Column(String, nullable=True)  # Deprecated
    city = Column(String, nullable=True)  # Deprecated - use postal_city
    state_province = Column(String, nullable=True)
    country = Column(String, default="South Africa", nullable=True)
    
    # Additional information
    birth_place = Column(String, nullable=True)
    
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