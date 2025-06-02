from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import json

from app import crud
from app.models.license import License


class ISOComplianceResult:
    """
    Represents the result of an ISO compliance check
    """
    def __init__(
        self,
        license_id: int,
        license_number: str,
        compliant: bool,
        compliance_score: float,
        iso_standard: str = "ISO_18013_1",
        issues: Optional[List[Dict[str, Any]]] = None,
        validations: Optional[Dict[str, Any]] = None,
        status: str = "compliant"
    ):
        self.license_id = license_id
        self.license_number = license_number
        self.compliant = compliant
        self.compliance_score = compliance_score
        self.iso_standard = iso_standard
        self.issues = issues or []
        self.validations = validations or {}
        self.status = status
        self.validation_date = datetime.utcnow()


class ISOComplianceCheckService:
    """
    Service for ISO 18013 compliance validation and checking logic.
    This service performs the actual compliance checks - notifications are handled separately.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> List[Dict[str, Any]]:
        """Load ISO validation rules"""
        return [
            {
                "id": "mrz_format_check",
                "name": "MRZ Format Validation",
                "category": "mrz",
                "iso_reference": "ISO 18013-1:2018 Section 4.2",
                "severity": "critical",
                "enabled": True,
                "auto_remediate": False
            },
            {
                "id": "security_features_check",
                "name": "Physical Security Features",
                "category": "security",
                "iso_reference": "ISO 18013-1:2018 Section 5.1",
                "severity": "major",
                "enabled": True,
                "auto_remediate": False
            },
            {
                "id": "biometric_quality_check",
                "name": "Biometric Template Quality",
                "category": "biometric",
                "iso_reference": "ISO 18013-5:2021 Section 6.2",
                "severity": "major",
                "enabled": True,
                "auto_remediate": True
            },
            {
                "id": "chip_data_integrity",
                "name": "Chip Data Integrity Check",
                "category": "chip",
                "iso_reference": "ISO 18013-3:2017 Section 4.3",
                "severity": "critical",
                "enabled": True,
                "auto_remediate": False
            },
            {
                "id": "digital_signature_validation",
                "name": "Digital Signature Validation",
                "category": "signature",
                "iso_reference": "ISO 18013-2:2020 Section 7.1",
                "severity": "critical",
                "enabled": True,
                "auto_remediate": False
            }
        ]

    def validate_license_compliance(
        self,
        license_id: int,
        iso_standard: str = "ISO_18013_1",
        full_validation: bool = True
    ) -> ISOComplianceResult:
        """
        Perform comprehensive ISO compliance validation on a license
        
        Returns:
            ISOComplianceResult containing validation results
        """
        license_record = crud.license.get(self.db, id=license_id)
        if not license_record:
            return ISOComplianceResult(
                license_id=license_id,
                license_number="UNKNOWN",
                compliant=False,
                compliance_score=0.0,
                status="critical_failure",
                issues=[{
                    "code": "LICENSE_NOT_FOUND",
                    "severity": "critical",
                    "description": "License record not found in database"
                }]
            )

        # Perform individual validations
        validations = {}
        issues = []
        
        if full_validation:
            validations = {
                "mrz_validation": self._validate_mrz(license_record),
                "security_features": self._validate_security_features(license_record),
                "biometric_validation": self._validate_biometric_data(license_record),
                "chip_data_validation": self._validate_chip_data(license_record),
                "digital_signature": self._validate_digital_signature(license_record),
                "physical_standards": self._validate_physical_standards(license_record)
            }
        else:
            # Quick validation - essential checks only
            validations = {
                "mrz_validation": self._validate_mrz(license_record),
                "chip_data_validation": self._validate_chip_data(license_record)
            }

        # Collect issues from all validations
        for validation_name, validation_result in validations.items():
            if not validation_result.get("valid", True):
                issues.extend(validation_result.get("issues", []))

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(validations)
        
        # Determine overall compliance status
        compliant = compliance_score >= 90.0 and not any(
            issue.get("severity") == "critical" for issue in issues
        )
        
        status = self._determine_compliance_status(compliance_score, issues)

        return ISOComplianceResult(
            license_id=license_id,
            license_number=license_record.license_number,
            compliant=compliant,
            compliance_score=compliance_score,
            iso_standard=iso_standard,
            issues=issues,
            validations=validations,
            status=status
        )

    def _validate_mrz(self, license_record: License) -> Dict[str, Any]:
        """Validate Machine Readable Zone (MRZ) compliance"""
        # Mock MRZ validation - would contain actual MRZ parsing and validation
        mrz_data = license_record.metadata.get("mrz_data") if license_record.metadata else None
        
        validation_result = {
            "valid": True,
            "format_valid": True,
            "checksum_valid": True,
            "data_consistency": True,
            "machine_readable": True,
            "iso_compliance_level": 5,
            "issues": []
        }

        # Mock validation logic
        if not mrz_data:
            validation_result.update({
                "valid": False,
                "format_valid": False,
                "issues": [{
                    "code": "MRZ_MISSING",
                    "severity": "critical",
                    "category": "mrz",
                    "description": "MRZ data not found in license metadata",
                    "iso_reference": "ISO 18013-1:2018 Section 4.2.1"
                }]
            })

        return validation_result

    def _validate_security_features(self, license_record: License) -> Dict[str, Any]:
        """Validate physical security features"""
        # Mock security features validation
        return {
            "valid": True,
            "hologram_present": True,
            "watermark_valid": True,
            "security_thread": True,
            "uv_features": True,
            "tactile_features": True,
            "microprinting": True,
            "security_score": 95,
            "tamper_evidence": True,
            "issues": []
        }

    def _validate_biometric_data(self, license_record: License) -> Dict[str, Any]:
        """Validate biometric data quality and compliance"""
        # Mock biometric validation
        return {
            "valid": True,
            "template_quality": 92,
            "iso_format_compliance": True,
            "facial_recognition_score": 88,
            "liveness_detection": True,
            "biometric_accuracy": 94,
            "issues": []
        }

    def _validate_chip_data(self, license_record: License) -> Dict[str, Any]:
        """Validate chip/RFID data integrity"""
        # Mock chip validation
        return {
            "valid": True,
            "chip_functional": True,
            "data_integrity": True,
            "access_control_valid": True,
            "cryptographic_binding": True,
            "lds_structure_valid": True,
            "dg_validation": {
                "DG1": True,  # MRZ data
                "DG2": True,  # Facial image
                "DG3": True,  # Fingerprints
                "DG14": True  # Security infos
            },
            "bac_functionality": True,
            "pace_functionality": True,
            "issues": []
        }

    def _validate_digital_signature(self, license_record: License) -> Dict[str, Any]:
        """Validate digital signature and certificate chain"""
        # Mock digital signature validation
        return {
            "valid": True,
            "signature_valid": True,
            "certificate_chain_valid": True,
            "timestamp_valid": True,
            "revocation_status": "valid",
            "signature_algorithm": "ECDSA",
            "hash_algorithm": "SHA-256",
            "signature_strength": 95,
            "issues": []
        }

    def _validate_physical_standards(self, license_record: License) -> Dict[str, Any]:
        """Validate physical card standards compliance"""
        # Mock physical standards validation
        return {
            "valid": True,
            "dimensions_correct": True,
            "material_compliance": True,
            "thickness_tolerance": True,
            "bend_test_passed": True,
            "temperature_resistance": True,
            "durability_score": 88,
            "print_quality": 92,
            "issues": []
        }

    def _calculate_compliance_score(self, validations: Dict[str, Any]) -> float:
        """Calculate overall compliance score from individual validations"""
        total_score = 0
        validation_count = 0
        
        weights = {
            "mrz_validation": 0.25,
            "security_features": 0.20,
            "biometric_validation": 0.20,
            "chip_data_validation": 0.15,
            "digital_signature": 0.15,
            "physical_standards": 0.05
        }

        for validation_name, validation_result in validations.items():
            if validation_name in weights:
                weight = weights[validation_name]
                
                # Extract score from validation result
                if "security_score" in validation_result:
                    score = validation_result["security_score"]
                elif "template_quality" in validation_result:
                    score = validation_result["template_quality"]
                elif "signature_strength" in validation_result:
                    score = validation_result["signature_strength"]
                elif "durability_score" in validation_result:
                    score = validation_result["durability_score"]
                elif validation_result.get("valid", False):
                    score = 100
                else:
                    score = 0

                total_score += score * weight
                validation_count += weight

        return round(total_score / validation_count if validation_count > 0 else 0, 2)

    def _determine_compliance_status(
        self, 
        compliance_score: float, 
        issues: List[Dict[str, Any]]
    ) -> str:
        """Determine compliance status based on score and issues"""
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        major_issues = [i for i in issues if i.get("severity") == "major"]

        if critical_issues:
            return "critical_failure"
        elif compliance_score < 70:
            return "non_compliant"
        elif major_issues or compliance_score < 90:
            return "non_compliant"
        else:
            return "compliant"

    def bulk_validate_licenses(
        self,
        license_ids: List[int],
        iso_standards: List[str],
        quick_scan: bool = False
    ) -> Dict[str, Any]:
        """
        Perform bulk compliance validation on multiple licenses
        
        Returns:
            Dict containing bulk validation results
        """
        results = {
            "total": len(license_ids),
            "compliant": 0,
            "non_compliant": 0,
            "critical_failures": 0,
            "validation_results": [],
            "summary": {
                "avg_compliance_score": 0.0,
                "common_issues": {},
                "processing_time": 0.0
            }
        }

        start_time = datetime.utcnow()
        total_score = 0

        for license_id in license_ids:
            for iso_standard in iso_standards:
                try:
                    validation_result = self.validate_license_compliance(
                        license_id, 
                        iso_standard,
                        full_validation=not quick_scan
                    )
                    
                    results["validation_results"].append({
                        "license_id": license_id,
                        "iso_standard": iso_standard,
                        "compliant": validation_result.compliant,
                        "compliance_score": validation_result.compliance_score,
                        "status": validation_result.status,
                        "issues_count": len(validation_result.issues)
                    })

                    # Update counters
                    if validation_result.status == "critical_failure":
                        results["critical_failures"] += 1
                    elif validation_result.compliant:
                        results["compliant"] += 1
                    else:
                        results["non_compliant"] += 1

                    total_score += validation_result.compliance_score

                    # Track common issues
                    for issue in validation_result.issues:
                        issue_code = issue.get("code", "UNKNOWN")
                        if issue_code in results["summary"]["common_issues"]:
                            results["summary"]["common_issues"][issue_code] += 1
                        else:
                            results["summary"]["common_issues"][issue_code] = 1

                except Exception as e:
                    results["critical_failures"] += 1

        # Calculate summary statistics
        total_validations = len(results["validation_results"])
        if total_validations > 0:
            results["summary"]["avg_compliance_score"] = round(total_score / total_validations, 2)

        end_time = datetime.utcnow()
        results["summary"]["processing_time"] = (end_time - start_time).total_seconds()

        return results

    def auto_remediate_compliance_issues(
        self,
        license_id: int,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Attempt to automatically fix compliance issues where possible
        
        Returns:
            Dict containing remediation results
        """
        remediation_results = {
            "license_id": license_id,
            "total_issues": len(issues),
            "issues_fixed": [],
            "issues_remaining": [],
            "auto_fix_success": False
        }

        for issue in issues:
            if issue.get("auto_fixable", False):
                # Attempt auto-remediation based on issue type
                success = self._attempt_auto_fix(license_id, issue)
                if success:
                    remediation_results["issues_fixed"].append(issue["code"])
                else:
                    remediation_results["issues_remaining"].append(issue["code"])
            else:
                remediation_results["issues_remaining"].append(issue["code"])

        remediation_results["auto_fix_success"] = len(remediation_results["issues_fixed"]) > 0

        return remediation_results

    def _attempt_auto_fix(self, license_id: int, issue: Dict[str, Any]) -> bool:
        """
        Attempt to automatically fix a specific compliance issue
        """
        issue_code = issue.get("code")
        
        # Mock auto-fix logic - would contain actual remediation procedures
        auto_fixable_issues = {
            "BIOMETRIC_QUALITY_LOW": self._fix_biometric_quality,
            "MRZ_CHECKSUM_ERROR": self._fix_mrz_checksum,
            "IMAGE_QUALITY_POOR": self._fix_image_quality
        }

        if issue_code in auto_fixable_issues:
            try:
                return auto_fixable_issues[issue_code](license_id, issue)
            except Exception:
                return False

        return False

    def _fix_biometric_quality(self, license_id: int, issue: Dict[str, Any]) -> bool:
        """Auto-fix biometric quality issues"""
        # Mock biometric quality enhancement
        return True

    def _fix_mrz_checksum(self, license_id: int, issue: Dict[str, Any]) -> bool:
        """Auto-fix MRZ checksum errors"""
        # Mock MRZ checksum recalculation
        return True

    def _fix_image_quality(self, license_id: int, issue: Dict[str, Any]) -> bool:
        """Auto-fix image quality issues"""
        # Mock image quality enhancement
        return True

    def get_compliance_statistics(self) -> Dict[str, Any]:
        """
        Get overall compliance statistics across the system
        """
        # Mock compliance statistics - would query actual database
        return {
            "total_licenses": 1250,
            "compliant_licenses": 1125,
            "non_compliant_licenses": 98,
            "pending_validation": 27,
            "critical_failures": 15,
            "compliance_rate": 90.0,
            "iso_18013_1_compliance": 92.5,
            "iso_18013_2_compliance": 88.2,
            "iso_18013_3_compliance": 91.7,
            "iso_18013_5_compliance": 87.9,
            "common_issues": [
                {"issue": "BIOMETRIC_QUALITY_LOW", "count": 45, "severity": "major"},
                {"issue": "SECURITY_FEATURE_MISSING", "count": 23, "severity": "major"},
                {"issue": "MRZ_FORMAT_ERROR", "count": 12, "severity": "critical"}
            ],
            "trend": {
                "weekly_compliance_rate": [88.5, 89.2, 90.1, 90.0],
                "improvement_trend": "stable"
            }
        } 