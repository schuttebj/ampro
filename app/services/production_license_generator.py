import io
import base64
import json
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pdf417gen
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm

from app.services.file_manager import file_manager, ISO_PHOTO_SPECS
from app.services.license_generator import (
    CARD_W_PX, CARD_H_PX, FONT_SIZES, COLORS,
    SALicenseGenerator, serialize_date
)

logger = logging.getLogger(__name__)

class ProductionLicenseGenerator:
    """
    Production-ready license generator with file management and ISO compliance
    """
    
    def __init__(self):
        self.sa_generator = SALicenseGenerator()
        self.version = "2.0"
    
    def generate_complete_license(self, license_data: Dict[str, Any], 
                                citizen_data: Dict[str, Any], 
                                force_regenerate: bool = False) -> Dict[str, str]:
        """
        Generate complete license package (front, back, combined PDF) and store files
        
        Args:
            license_data: License information
            citizen_data: Citizen information including photo
            force_regenerate: Force regeneration even if files exist
        
        Returns:
            Dictionary with file paths and URLs
        """
        license_id = license_data["id"]
        citizen_id = citizen_data["id"]
        
        try:
            # Process photo first
            processed_photo_path = self._ensure_processed_photo(citizen_data)
            
            # Check if regeneration is needed
            if not force_regenerate and self._files_exist(license_id):
                return self._get_existing_file_info(license_id)
            
            # Clean up old license files before generating new ones
            file_manager.cleanup_old_license_files(license_id)
            
            # Generate license images
            front_image = self._generate_front_image(license_data, citizen_data, processed_photo_path)
            back_image = self._generate_back_image(license_data, citizen_data)
            
            # Save image files
            front_path = file_manager.save_license_file(
                license_id, "front", front_image, "png"
            )
            back_path = file_manager.save_license_file(
                license_id, "back", back_image, "png"
            )
            
            # Generate PDFs
            front_pdf = self._generate_pdf(front_image, f"License {license_data['license_number']} - Front")
            back_pdf = self._generate_pdf(back_image, f"License {license_data['license_number']} - Back")
            combined_pdf = self._generate_combined_pdf(front_image, back_image, license_data)
            
            # Save PDF files
            front_pdf_path = file_manager.save_license_file(
                license_id, "front", front_pdf, "pdf"
            )
            back_pdf_path = file_manager.save_license_file(
                license_id, "back", back_pdf, "pdf"
            )
            combined_pdf_path = file_manager.save_license_file(
                license_id, "combined", combined_pdf, "pdf"
            )
            
            # Return file information
            result = {
                "front_image_path": front_path,
                "back_image_path": back_path,
                "front_pdf_path": front_pdf_path,
                "back_pdf_path": back_pdf_path,
                "combined_pdf_path": combined_pdf_path,
                "front_image_url": file_manager.get_file_url(front_path),
                "back_image_url": file_manager.get_file_url(back_path),
                "front_pdf_url": file_manager.get_file_url(front_pdf_path),
                "back_pdf_url": file_manager.get_file_url(back_pdf_path),
                "combined_pdf_url": file_manager.get_file_url(combined_pdf_path),
                "processed_photo_path": processed_photo_path,
                "processed_photo_url": file_manager.get_file_url(processed_photo_path),
                "generation_timestamp": datetime.now().isoformat(),
                "generator_version": self.version
            }
            
            logger.info(f"Successfully generated complete license package for license {license_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating license {license_id}: {str(e)}")
            raise
    
    def _ensure_processed_photo(self, citizen_data: Dict[str, Any]) -> str:
        """
        Ensure citizen has a processed photo that meets ISO specifications
        
        Args:
            citizen_data: Citizen information
        
        Returns:
            Path to processed photo
        """
        citizen_id = citizen_data["id"]
        photo_url = citizen_data.get("photo_url")
        existing_processed_path = citizen_data.get("processed_photo_path")
        
        # Check if we already have a valid processed photo
        if existing_processed_path and file_manager.file_exists(existing_processed_path):
            return existing_processed_path
        
        # Download and process new photo
        if photo_url:
            # Clean up old photos before processing new one
            file_manager.cleanup_old_files(citizen_id)
            
            original_path, processed_path = file_manager.download_and_store_photo(
                photo_url, citizen_id
            )
            
            logger.info(f"Processed new photo for citizen {citizen_id}")
            return processed_path
        
        # No photo available - this should be handled by the caller
        raise ValueError(f"No photo available for citizen {citizen_id}")
    
    def _generate_front_image(self, license_data: Dict[str, Any], 
                            citizen_data: Dict[str, Any], 
                            photo_path: str) -> bytes:
        """Generate front side image"""
        # Read processed photo
        photo_content = file_manager.get_file_content(photo_path)
        photo_base64 = base64.b64encode(photo_content).decode('utf-8')
        
        # Generate using SA generator
        front_image_base64 = self.sa_generator.generate_front(license_data, photo_base64)
        
        # Convert back to bytes
        return base64.b64decode(front_image_base64)
    
    def _generate_back_image(self, license_data: Dict[str, Any], 
                           citizen_data: Dict[str, Any]) -> bytes:
        """Generate back side image"""
        back_image_base64 = self.sa_generator.generate_back(license_data)
        return base64.b64decode(back_image_base64)
    
    def _generate_pdf(self, image_bytes: bytes, title: str) -> bytes:
        """
        Generate PDF from image bytes
        
        Args:
            image_bytes: Image content as bytes
            title: PDF title
        
        Returns:
            PDF content as bytes
        """
        pdf_buffer = io.BytesIO()
        
        # Create PDF with exact card dimensions
        page_width = CARD_W_PX * 72 / 300  # Convert to points (72 DPI)
        page_height = CARD_H_PX * 72 / 300
        
        c = canvas.Canvas(pdf_buffer, pagesize=(page_width, page_height))
        c.setTitle(title)
        
        # Create temporary image file for PDF
        img_buffer = io.BytesIO(image_bytes)
        
        # Add image to PDF
        c.drawImage(
            img_buffer, 0, 0,
            width=page_width, height=page_height,
            preserveAspectRatio=True
        )
        
        c.save()
        return pdf_buffer.getvalue()
    
    def _generate_combined_pdf(self, front_bytes: bytes, back_bytes: bytes, 
                              license_data: Dict[str, Any]) -> bytes:
        """
        Generate combined PDF with both front and back
        
        Args:
            front_bytes: Front image bytes
            back_bytes: Back image bytes
            license_data: License information
        
        Returns:
            Combined PDF as bytes
        """
        pdf_buffer = io.BytesIO()
        
        # Create PDF with exact card dimensions
        page_width = CARD_W_PX * 72 / 300  # Convert to points (72 DPI)
        page_height = CARD_H_PX * 72 / 300
        
        c = canvas.Canvas(pdf_buffer, pagesize=(page_width, page_height))
        c.setTitle(f"South African Driver's License - {license_data['license_number']}")
        
        # Add metadata
        c.setAuthor("AMPRO License System")
        c.setSubject("Official South African Driver's License")
        c.setCreator("AMPRO Production Generator v2.0")
        
        # Front page
        front_buffer = io.BytesIO(front_bytes)
        c.drawImage(
            front_buffer, 0, 0,
            width=page_width, height=page_height,
            preserveAspectRatio=True
        )
        c.showPage()
        
        # Back page
        back_buffer = io.BytesIO(back_bytes)
        c.drawImage(
            back_buffer, 0, 0,
            width=page_width, height=page_height,
            preserveAspectRatio=True
        )
        
        c.save()
        return pdf_buffer.getvalue()
    
    def _files_exist(self, license_id: int) -> bool:
        """Check if all license files exist"""
        required_files = [
            f"licenses/license_{license_id}_front.png",
            f"licenses/license_{license_id}_back.png",
            f"licenses/license_{license_id}_combined.pdf"
        ]
        
        return all(file_manager.file_exists(path) for path in required_files)
    
    def _get_existing_file_info(self, license_id: int) -> Dict[str, str]:
        """Get information about existing files"""
        paths = {
            "front_image_path": f"licenses/license_{license_id}_front.png",
            "back_image_path": f"licenses/license_{license_id}_back.png",
            "front_pdf_path": f"licenses/license_{license_id}_front.pdf",
            "back_pdf_path": f"licenses/license_{license_id}_back.pdf",
            "combined_pdf_path": f"licenses/license_{license_id}_combined.pdf",
        }
        
        result = {}
        for key, path in paths.items():
            if file_manager.file_exists(path):
                result[key] = path
                result[key.replace("_path", "_url")] = file_manager.get_file_url(path)
        
        result["generation_timestamp"] = datetime.now().isoformat()
        result["generator_version"] = self.version
        result["from_cache"] = True
        
        return result
    
    def generate_preview_only(self, license_data: Dict[str, Any], 
                            citizen_data: Dict[str, Any], 
                            side: str = "front") -> str:
        """
        Generate preview without storing files (for quick previews)
        
        Args:
            license_data: License information
            citizen_data: Citizen information
            side: "front" or "back"
        
        Returns:
            Base64 encoded image
        """
        try:
            if side == "front":
                # Process photo for preview
                photo_url = citizen_data.get("photo_url")
                photo_base64 = None
                
                if photo_url:
                    # For preview, we can use existing processed photo or process temporarily
                    processed_path = citizen_data.get("processed_photo_path")
                    if processed_path and file_manager.file_exists(processed_path):
                        photo_content = file_manager.get_file_content(processed_path)
                        photo_base64 = base64.b64encode(photo_content).decode('utf-8')
                
                return self.sa_generator.generate_front(license_data, photo_base64)
            else:
                return self.sa_generator.generate_back(license_data)
                
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}")
            raise
    
    def update_citizen_photo(self, citizen_id: int, photo_url: str) -> Tuple[str, str]:
        """
        Update citizen photo and return new paths
        
        Args:
            citizen_id: Citizen ID
            photo_url: New photo URL
        
        Returns:
            Tuple of (original_path, processed_path)
        """
        try:
            # Clean up old photos
            file_manager.cleanup_old_files(citizen_id)
            
            # Download and process new photo
            original_path, processed_path = file_manager.download_and_store_photo(
                photo_url, citizen_id
            )
            
            logger.info(f"Updated photo for citizen {citizen_id}")
            return original_path, processed_path
            
        except Exception as e:
            logger.error(f"Error updating citizen photo {citizen_id}: {str(e)}")
            raise


# Global instance
production_generator = ProductionLicenseGenerator() 