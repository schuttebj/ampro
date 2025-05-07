from typing import List, Optional
from datetime import date
import uuid

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.license import License, LicenseApplication, LicenseStatus, ApplicationStatus
from app.schemas.license import LicenseCreate, LicenseUpdate, LicenseApplicationCreate, LicenseApplicationUpdate


class CRUDLicense(CRUDBase[License, LicenseCreate, LicenseUpdate]):
    """
    CRUD operations for License model.
    """
    def get_by_license_number(self, db: Session, *, license_number: str) -> Optional[License]:
        """
        Get a license by license number.
        """
        return db.query(License).filter(License.license_number == license_number).first()

    def get_by_citizen_id(self, db: Session, *, citizen_id: int, skip: int = 0, limit: int = 100) -> List[License]:
        """
        Get all licenses for a citizen.
        """
        return db.query(License).filter(License.citizen_id == citizen_id).offset(skip).limit(limit).all()

    def get_by_status(self, db: Session, *, status: LicenseStatus, skip: int = 0, limit: int = 100) -> List[License]:
        """
        Get all licenses with a specific status.
        """
        return db.query(License).filter(License.status == status).offset(skip).limit(limit).all()
    
    def get_expired_licenses(self, db: Session, *, cutoff_date: date = date.today(), skip: int = 0, limit: int = 100) -> List[License]:
        """
        Get all licenses that are expired as of the cutoff date.
        """
        return (db.query(License)
                .filter(License.expiry_date <= cutoff_date)
                .filter(License.status != LicenseStatus.EXPIRED)
                .offset(skip).limit(limit).all())
    
    def generate_license_number(self) -> str:
        """
        Generate a unique license number.
        """
        # Format: L-XXXX-XXXX-XXXX (X = alphanumeric)
        # Could be enhanced with more specific logic based on requirements
        unique_id = uuid.uuid4().hex[:12].upper()
        return f"L-{unique_id[:4]}-{unique_id[4:8]}-{unique_id[8:12]}"


class CRUDLicenseApplication(CRUDBase[LicenseApplication, LicenseApplicationCreate, LicenseApplicationUpdate]):
    """
    CRUD operations for LicenseApplication model.
    """
    def get_by_citizen_id(self, db: Session, *, citizen_id: int, skip: int = 0, limit: int = 100) -> List[LicenseApplication]:
        """
        Get all applications for a citizen.
        """
        return db.query(LicenseApplication).filter(LicenseApplication.citizen_id == citizen_id).offset(skip).limit(limit).all()

    def get_by_status(self, db: Session, *, status: ApplicationStatus, skip: int = 0, limit: int = 100) -> List[LicenseApplication]:
        """
        Get all applications with a specific status.
        """
        return db.query(LicenseApplication).filter(LicenseApplication.status == status).offset(skip).limit(limit).all()
    
    def get_by_reviewer(self, db: Session, *, reviewer_id: int, skip: int = 0, limit: int = 100) -> List[LicenseApplication]:
        """
        Get all applications reviewed by a specific user.
        """
        return db.query(LicenseApplication).filter(LicenseApplication.reviewed_by == reviewer_id).offset(skip).limit(limit).all()
    
    def get_pending_review(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[LicenseApplication]:
        """
        Get all applications pending review.
        """
        return (db.query(LicenseApplication)
                .filter(LicenseApplication.status == ApplicationStatus.SUBMITTED)
                .offset(skip).limit(limit).all())


license = CRUDLicense(License)
license_application = CRUDLicenseApplication(LicenseApplication) 