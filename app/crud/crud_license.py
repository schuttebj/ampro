from typing import List, Optional, Dict, Any
from datetime import date, datetime
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
    
    def get_multi_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[License]:
        """
        Get all active licenses (not soft-deleted).
        """
        return (
            db.query(self.model)
            .filter(License.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
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
    
    def update_file_paths(self, db: Session, *, license_id: int, file_paths: Dict[str, str]) -> Optional[License]:
        """
        Update license file paths after generation
        
        Args:
            db: Database session
            license_id: License ID
            file_paths: Dictionary with file path keys and values
        
        Returns:
            Updated license object
        """
        license_obj = self.get(db, id=license_id)
        if not license_obj:
            return None
        
        # Update file paths
        update_data = {
            "last_generated": datetime.now(),
            "generation_version": file_paths.get("generator_version", "2.0")
        }
        
        # Map file paths
        path_mapping = {
            "front_image_path": "front_image_path",
            "back_image_path": "back_image_path", 
            "front_pdf_path": "front_pdf_path",
            "back_pdf_path": "back_pdf_path",
            "combined_pdf_path": "combined_pdf_path",
            "processed_photo_path": "processed_photo_path"
        }
        
        for key, db_field in path_mapping.items():
            if key in file_paths:
                update_data[db_field] = file_paths[key]
        
        return self.update(db, db_obj=license_obj, obj_in=update_data)
    
    def get_licenses_needing_regeneration(self, db: Session, *, 
                                        version_cutoff: str = "1.0", 
                                        skip: int = 0, 
                                        limit: int = 100) -> List[License]:
        """
        Get licenses that need regeneration due to version updates
        
        Args:
            db: Database session
            version_cutoff: Minimum version required
            skip: Records to skip
            limit: Maximum records to return
        
        Returns:
            List of licenses needing regeneration
        """
        return (db.query(License)
                .filter(
                    (License.generation_version < version_cutoff) |
                    (License.generation_version.is_(None)) |
                    (License.last_generated.is_(None))
                )
                .offset(skip)
                .limit(limit)
                .all())
    
    def mark_for_regeneration(self, db: Session, *, license_id: int) -> Optional[License]:
        """
        Mark a license for regeneration by clearing generation timestamp
        
        Args:
            db: Database session
            license_id: License ID
        
        Returns:
            Updated license object
        """
        license_obj = self.get(db, id=license_id)
        if not license_obj:
            return None
        
        update_data = {
            "last_generated": None,
            "generation_version": "1.0"  # Force regeneration
        }
        
        return self.update(db, db_obj=license_obj, obj_in=update_data)


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