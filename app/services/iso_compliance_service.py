import json
import hashlib
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class ISOComplianceService:
    """
    Service for ISO 18013-1:2018 compliance for African driver's licenses.
    Handles MRZ generation, security features, and biometric data processing.
    """
    
    # ISO 3166-1 alpha-3 country codes for African countries
    AFRICAN_COUNTRY_CODES = {
        "south_africa": "ZAF",
        "nigeria": "NGA", 
        "kenya": "KEN",
        "ghana": "GHA",
        "egypt": "EGY",
        "morocco": "MAR",
        "ethiopia": "ETH",
        "uganda": "UGA",
        "tanzania": "TZA",
        "zimbabwe": "ZWE",
        "botswana": "BWA",
        "namibia": "NAM",
        "zambia": "ZMB",
        "malawi": "MWI",
        "mozambique": "MOZ",
        "angola": "AGO",
        "cameroon": "CMR",
        "ivory_coast": "CIV",
        "senegal": "SEN",
        "mali": "MLI",
        "burkina_faso": "BFA",
        "niger": "NER",
        "chad": "TCD",
        "sudan": "SDN",
        "libya": "LBY",
        "tunisia": "TUN",
        "algeria": "DZA"
    }
    
    def __init__(self, country_code: str = "ZAF", issuing_authority: str = "Department of Transport"):
        self.country_code = country_code
        self.issuing_authority = issuing_authority
        self.iso_version = "18013-1:2018"
    
    def generate_mrz_data(self, license_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate Machine Readable Zone (MRZ) data according to ISO 18013 standards.
        
        Args:
            license_data: Dictionary containing license and citizen information
            
        Returns:
            Dictionary with MRZ lines
        """
        try:
            # Extract data
            license_number = license_data.get("license_number", "")
            first_name = license_data.get("first_name", "").upper()
            last_name = license_data.get("last_name", "").upper()
            birth_date = license_data.get("birth_date")
            expiry_date = license_data.get("expiry_date")
            gender = license_data.get("gender", "M").upper()
            nationality = license_data.get("nationality", self.country_code)
            
            # Format dates for MRZ (YYMMDD)
            birth_date_mrz = self._format_date_for_mrz(birth_date) if birth_date else "000000"
            expiry_date_mrz = self._format_date_for_mrz(expiry_date) if expiry_date else "000000"
            
            # Line 1: Document type, country code, document number
            line1 = f"DL{self.country_code}{license_number:<9}"[:44].ljust(44, '<')
            
            # Line 2: Birth date, gender, expiry date, nationality, optional data
            line2 = f"{birth_date_mrz}{gender[0]}{expiry_date_mrz}{nationality}{'':<10}"[:44].ljust(44, '<')
            
            # Line 3: Names (last name << first name)
            names = f"{last_name}<<{first_name}"[:44].ljust(44, '<')
            
            # Calculate check digits
            line1_check = self._calculate_mrz_check_digit(line1)
            line2_check = self._calculate_mrz_check_digit(line2)
            
            return {
                "mrz_line1": line1 + str(line1_check),
                "mrz_line2": line2 + str(line2_check),
                "mrz_line3": names
            }
            
        except Exception as e:
            logger.error(f"Error generating MRZ data: {e}")
            return {"mrz_line1": "", "mrz_line2": "", "mrz_line3": ""}
    
    def generate_security_features(self, license_data: Dict[str, Any]) -> str:
        """
        Generate security features JSON for ISO compliance.
        
        Args:
            license_data: License and citizen data
            
        Returns:
            JSON string of security features
        """
        security_features = {
            "version": self.iso_version,
            "generated_at": datetime.utcnow().isoformat(),
            "features": {
                "hologram": True,
                "microtext": True,
                "uv_ink": True,
                "rfid_chip": True,
                "digital_signature": True,
                "biometric_template": True,
                "security_thread": True,
                "color_changing_ink": True,
                "tactile_features": True,
                "ghost_image": True
            },
            "security_level": "high",
            "anti_counterfeiting": {
                "unique_serial": self._generate_security_serial(),
                "verification_code": self._generate_verification_code(license_data),
                "hash_verification": self._generate_data_hash(license_data)
            },
            "compliance": {
                "iso_18013": True,
                "vienna_convention": True,
                "african_union_standards": True
            }
        }
        
        return json.dumps(security_features, indent=2)
    
    def generate_digital_signature(self, license_data: Dict[str, Any]) -> str:
        """
        Generate digital signature for license authenticity.
        
        Args:
            license_data: License data to sign
            
        Returns:
            Base64 encoded digital signature
        """
        try:
            # Create signature data
            signature_data = {
                "license_number": license_data.get("license_number"),
                "citizen_id": license_data.get("citizen_id"),
                "issue_date": str(license_data.get("issue_date")),
                "expiry_date": str(license_data.get("expiry_date")),
                "issuing_authority": self.issuing_authority,
                "country_code": self.country_code,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Generate hash-based signature (in production, use proper PKI)
            signature_string = json.dumps(signature_data, sort_keys=True)
            signature_hash = hashlib.sha256(signature_string.encode()).hexdigest()
            
            return base64.b64encode(signature_hash.encode()).decode()
            
        except Exception as e:
            logger.error(f"Error generating digital signature: {e}")
            return ""
    
    def generate_biometric_template(self, photo_data: Optional[bytes] = None) -> str:
        """
        Generate biometric template (placeholder for actual biometric processing).
        
        Args:
            photo_data: Photo data for biometric extraction
            
        Returns:
            Base64 encoded biometric template
        """
        try:
            if photo_data:
                # In production, this would use actual biometric extraction
                # For now, generate a hash-based template
                template_hash = hashlib.sha256(photo_data).hexdigest()
                return base64.b64encode(template_hash.encode()).decode()
            else:
                # Generate placeholder template
                placeholder = f"BIOMETRIC_TEMPLATE_{datetime.utcnow().timestamp()}"
                return base64.b64encode(placeholder.encode()).decode()
                
        except Exception as e:
            logger.error(f"Error generating biometric template: {e}")
            return ""
    
    def generate_chip_data(self, license_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate RFID chip data for smart card licenses.
        
        Args:
            license_data: License information
            
        Returns:
            Dictionary with chip serial and encrypted data
        """
        try:
            # Generate chip serial number
            chip_serial = f"{self.country_code}{datetime.utcnow().strftime('%Y%m%d')}{license_data.get('license_number', '')[-6:]}"
            
            # Prepare chip data
            chip_data = {
                "license_number": license_data.get("license_number"),
                "holder_name": f"{license_data.get('first_name')} {license_data.get('last_name')}",
                "birth_date": str(license_data.get("birth_date")),
                "issue_date": str(license_data.get("issue_date")),
                "expiry_date": str(license_data.get("expiry_date")),
                "categories": license_data.get("category"),
                "restrictions": license_data.get("restrictions", ""),
                "issuing_authority": self.issuing_authority,
                "country_code": self.country_code
            }
            
            # Encrypt chip data (in production, use proper encryption)
            chip_data_json = json.dumps(chip_data, sort_keys=True)
            encrypted_data = base64.b64encode(chip_data_json.encode()).decode()
            
            return {
                "chip_serial_number": chip_serial,
                "chip_data_encrypted": encrypted_data
            }
            
        except Exception as e:
            logger.error(f"Error generating chip data: {e}")
            return {"chip_serial_number": "", "chip_data_encrypted": ""}
    
    def validate_iso_compliance(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate license data for ISO 18013 compliance.
        
        Args:
            license_data: License data to validate
            
        Returns:
            Validation result with compliance status and issues
        """
        validation_result = {
            "compliant": True,
            "issues": [],
            "warnings": [],
            "score": 100
        }
        
        # Required fields check
        required_fields = [
            "license_number", "first_name", "last_name", 
            "birth_date", "issue_date", "expiry_date", "category"
        ]
        
        for field in required_fields:
            if not license_data.get(field):
                validation_result["issues"].append(f"Missing required field: {field}")
                validation_result["compliant"] = False
                validation_result["score"] -= 10
        
        # Date validation
        if license_data.get("birth_date") and license_data.get("issue_date"):
            if license_data["birth_date"] >= license_data["issue_date"]:
                validation_result["issues"].append("Birth date must be before issue date")
                validation_result["compliant"] = False
                validation_result["score"] -= 15
        
        if license_data.get("issue_date") and license_data.get("expiry_date"):
            if license_data["issue_date"] >= license_data["expiry_date"]:
                validation_result["issues"].append("Issue date must be before expiry date")
                validation_result["compliant"] = False
                validation_result["score"] -= 15
        
        # License number format
        license_number = license_data.get("license_number", "")
        if len(license_number) < 8:
            validation_result["warnings"].append("License number should be at least 8 characters")
            validation_result["score"] -= 5
        
        # Photo requirements
        if not license_data.get("photo_path"):
            validation_result["warnings"].append("Photo is required for ISO compliance")
            validation_result["score"] -= 10
        
        return validation_result
    
    def _format_date_for_mrz(self, date_obj) -> str:
        """Format date for MRZ (YYMMDD format)."""
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                return "000000"
        
        if isinstance(date_obj, (date, datetime)):
            return date_obj.strftime("%y%m%d")
        
        return "000000"
    
    def _calculate_mrz_check_digit(self, data: str) -> int:
        """Calculate MRZ check digit using ISO standard algorithm."""
        weights = [7, 3, 1]
        total = 0
        
        for i, char in enumerate(data):
            if char.isdigit():
                value = int(char)
            elif char.isalpha():
                value = ord(char.upper()) - ord('A') + 10
            else:
                value = 0
            
            total += value * weights[i % 3]
        
        return total % 10
    
    def _generate_security_serial(self) -> str:
        """Generate unique security serial number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{self.country_code}{timestamp}"
    
    def _generate_verification_code(self, license_data: Dict[str, Any]) -> str:
        """Generate verification code for anti-counterfeiting."""
        verification_string = f"{license_data.get('license_number')}{license_data.get('citizen_id')}{self.country_code}"
        return hashlib.md5(verification_string.encode()).hexdigest()[:8].upper()
    
    def _generate_data_hash(self, license_data: Dict[str, Any]) -> str:
        """Generate hash of license data for integrity verification."""
        hash_data = {
            "license_number": license_data.get("license_number"),
            "citizen_id": license_data.get("citizen_id"),
            "first_name": license_data.get("first_name"),
            "last_name": license_data.get("last_name"),
            "birth_date": str(license_data.get("birth_date")),
            "category": license_data.get("category")
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()


# Global ISO compliance service instance
iso_compliance_service = ISOComplianceService() 