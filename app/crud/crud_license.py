from typing import List, Optional, Dict, Any
from datetime import date, datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.crud.base import CRUDBase
from app.models.license import License, LicenseApplication, LicenseFee, Payment
from app.models.license import LicenseStatus, ApplicationStatus, LicenseCategory, TransactionType, ApplicationType, PaymentStatus
from app.schemas.license import (
    LicenseCreate, LicenseUpdate, 
    LicenseApplicationCreate, LicenseApplicationUpdate,
    LicenseFeeCreate, LicenseFeeUpdate,
    PaymentCreate, PaymentUpdate
)


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
            "watermark_image_path": "watermark_image_path",
            "front_pdf_path": "front_pdf_path",
            "back_pdf_path": "back_pdf_path",
            "watermark_pdf_path": "watermark_pdf_path",
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
                .filter(LicenseApplication.status == ApplicationStatus.SUBMITTED.value)
                .offset(skip).limit(limit).all())

    def get_pending_applications(self, db: Session, skip: int = 0, limit: int = 100) -> List[LicenseApplication]:
        return db.query(LicenseApplication).filter(
            or_(
                LicenseApplication.status == ApplicationStatus.SUBMITTED,
                LicenseApplication.status == ApplicationStatus.UNDER_REVIEW,
                LicenseApplication.status == ApplicationStatus.PENDING_DOCUMENTS
            )
        ).offset(skip).limit(limit).all()

    def get_draft_applications(self, db: Session, *, citizen_id: int = None, skip: int = 0, limit: int = 100) -> List[LicenseApplication]:
        query = db.query(LicenseApplication).filter(
            and_(
                LicenseApplication.is_draft == True,
                LicenseApplication.status == ApplicationStatus.APPLIED
            )
        )
        if citizen_id:
            query = query.filter(LicenseApplication.citizen_id == citizen_id)
        return query.offset(skip).limit(limit).all()

    def submit_application(self, db: Session, *, application_id: int) -> Optional[LicenseApplication]:
        """Submit a draft application."""
        application = self.get(db, id=application_id)
        if application and application.is_draft:
            application.is_draft = False
            application.status = ApplicationStatus.SUBMITTED
            application.submitted_at = datetime.utcnow()
            db.add(application)
            db.commit()
            db.refresh(application)
        return application

    def update_status(self, db: Session, *, application_id: int, status: ApplicationStatus) -> Optional[LicenseApplication]:
        """Update application status."""
        application = self.get(db, id=application_id)
        if application:
            application.status = status
            application.last_updated = datetime.utcnow()
            db.add(application)
            db.commit()
            db.refresh(application)
        return application


class CRUDLicenseFee(CRUDBase[LicenseFee, LicenseFeeCreate, LicenseFeeUpdate]):
    def get_by_category_and_type(
        self, 
        db: Session, 
        *, 
        license_category: LicenseCategory,
        transaction_type: TransactionType,
        application_type: ApplicationType
    ) -> Optional[LicenseFee]:
        """Get fee for specific license category, transaction type, and application type."""
        return db.query(LicenseFee).filter(
            and_(
                LicenseFee.license_category == license_category,
                LicenseFee.transaction_type == transaction_type,
                LicenseFee.application_type == application_type,
                LicenseFee.is_active == True
            )
        ).first()

    def get_active_fees(self, db: Session, skip: int = 0, limit: int = 100) -> List[LicenseFee]:
        """Get all active fees."""
        return db.query(LicenseFee).filter(LicenseFee.is_active == True).offset(skip).limit(limit).all()

    def get_fees_by_category(self, db: Session, *, license_category: LicenseCategory) -> List[LicenseFee]:
        """Get all fees for a specific license category."""
        return db.query(LicenseFee).filter(
            and_(
                LicenseFee.license_category == license_category,
                LicenseFee.is_active == True
            )
        ).all()

    def calculate_fee_for_application(
        self,
        db: Session,
        *,
        license_category: LicenseCategory,
        transaction_type: TransactionType,
        application_type: ApplicationType,
        applicant_age: Optional[int] = None
    ) -> Optional[int]:
        """Calculate total fee for an application."""
        fee = self.get_by_category_and_type(
            db, 
            license_category=license_category,
            transaction_type=transaction_type,
            application_type=application_type
        )
        
        if not fee:
            return None
            
        # Check age requirements if specified
        if applicant_age is not None and (fee.minimum_age or fee.maximum_age):
            if fee.minimum_age and applicant_age < fee.minimum_age:
                return None
            if fee.maximum_age and applicant_age > fee.maximum_age:
                return None
                
        return fee.total_fee()


class CRUDPayment(CRUDBase[Payment, PaymentCreate, PaymentUpdate]):
    def get_by_application_id(self, db: Session, *, application_id: int) -> List[Payment]:
        """Get all payments for an application."""
        return db.query(Payment).filter(Payment.application_id == application_id).all()

    def get_by_reference(self, db: Session, *, payment_reference: str) -> Optional[Payment]:
        """Get payment by reference number."""
        return db.query(Payment).filter(Payment.payment_reference == payment_reference).first()

    def get_pending_payments(self, db: Session, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get all pending payments."""
        return db.query(Payment).filter(Payment.status == PaymentStatus.PENDING).offset(skip).limit(limit).all()

    def mark_as_paid(self, db: Session, *, payment_id: int, processed_by_user_id: int) -> Optional[Payment]:
        """Mark payment as paid."""
        payment = self.get(db, id=payment_id)
        if payment:
            payment.status = PaymentStatus.PAID
            payment.payment_date = datetime.utcnow()
            payment.processed_at = datetime.utcnow()
            payment.processed_by_user_id = processed_by_user_id
            db.add(payment)
            db.commit()
            db.refresh(payment)
        return payment

    def generate_payment_reference(self, db: Session) -> str:
        """Generate unique payment reference."""
        import random
        import string
        from datetime import datetime
        
        # Format: PAY-YYYYMMDD-XXXXX
        date_part = datetime.utcnow().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.digits, k=5))
        reference = f"PAY-{date_part}-{random_part}"
        
        # Ensure uniqueness
        while self.get_by_reference(db, payment_reference=reference):
            random_part = ''.join(random.choices(string.digits, k=5))
            reference = f"PAY-{date_part}-{random_part}"
            
        return reference


# Create instances
license = CRUDLicense(License)
license_application = CRUDLicenseApplication(LicenseApplication)
license_fee = CRUDLicenseFee(LicenseFee)
payment = CRUDPayment(Payment) 