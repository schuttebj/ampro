import io
import base64
import json
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging
import uuid

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
        Generate complete license package (front, back, combined PDF with watermark) and store files
        
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
            
            # Generate watermark as separate image
            watermark_image = self._generate_watermark_image(license_data)
            
            # Save image files
            front_path = file_manager.save_license_file(
                license_id, "front", front_image, "png"
            )
            back_path = file_manager.save_license_file(
                license_id, "back", back_image, "png"
            )
            watermark_path = file_manager.save_license_file(
                license_id, "watermark", watermark_image, "png"
            )
            
            # Generate PDFs
            front_pdf = self._generate_pdf(front_image, f"License {license_data['license_number']} - Front")
            back_pdf = self._generate_pdf(back_image, f"License {license_data['license_number']} - Back")
            watermark_pdf = self._generate_pdf(watermark_image, f"License {license_data['license_number']} - Watermark")
            combined_pdf = self._generate_combined_pdf_with_watermark(front_image, back_image, watermark_image, license_data)
            
            # Save PDF files
            front_pdf_path = file_manager.save_license_file(
                license_id, "front", front_pdf, "pdf"
            )
            back_pdf_path = file_manager.save_license_file(
                license_id, "back", back_pdf, "pdf"
            )
            watermark_pdf_path = file_manager.save_license_file(
                license_id, "watermark", watermark_pdf, "pdf"
            )
            combined_pdf_path = file_manager.save_license_file(
                license_id, "combined", combined_pdf, "pdf"
            )
            
            # Return file information
            result = {
                "front_image_path": front_path,
                "back_image_path": back_path,
                "watermark_image_path": watermark_path,
                "front_pdf_path": front_pdf_path,
                "back_pdf_path": back_pdf_path,
                "watermark_pdf_path": watermark_pdf_path,
                "combined_pdf_path": combined_pdf_path,
                "front_image_url": file_manager.get_file_url(front_path),
                "back_image_url": file_manager.get_file_url(back_path),
                "watermark_image_url": file_manager.get_file_url(watermark_path),
                "front_pdf_url": file_manager.get_file_url(front_pdf_path),
                "back_pdf_url": file_manager.get_file_url(back_pdf_path),
                "watermark_pdf_url": file_manager.get_file_url(watermark_pdf_path),
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
            logger.info(f"Using existing processed photo at {existing_processed_path}")
            return existing_processed_path
        
        # If we have a processed path but file doesn't exist, log this
        if existing_processed_path:
            logger.warning(f"Processed photo path exists in DB but file not found: {existing_processed_path}")
        
        # Download and process new photo if URL is available
        if photo_url:
            try:
                # Clean up old photos before processing new one
                file_manager.cleanup_old_files(citizen_id)
                
                original_path, processed_path = file_manager.download_and_store_photo(
                    photo_url, citizen_id
                )
                
                logger.info(f"Processed new photo for citizen {citizen_id}")
                return processed_path
            except Exception as e:
                logger.error(f"Error processing photo from URL {photo_url}: {str(e)}")
                # We'll try to create a placeholder instead of falling back to a nonexistent path
                placeholder_path = self._create_placeholder_photo(citizen_id)
                if placeholder_path:
                    return placeholder_path
                raise
        
        # If we got here, try to create a placeholder image
        placeholder_path = self._create_placeholder_photo(citizen_id)
        if placeholder_path:
            return placeholder_path
            
        # No photo available - this should be handled by the caller
        raise ValueError(f"No photo available for citizen {citizen_id}")
    
    def _create_placeholder_photo(self, citizen_id: int) -> Optional[str]:
        """
        Create a placeholder photo for a citizen
        
        Args:
            citizen_id: Citizen ID
            
        Returns:
            Path to placeholder photo or None if creation failed
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a blank image with ISO photo specs
            width = ISO_PHOTO_SPECS["width_px"]
            height = ISO_PHOTO_SPECS["height_px"]
            img = Image.new('RGB', (width, height), color=(240, 240, 240))
            
            # Add text "No Photo" to the image
            draw = ImageDraw.Draw(img)
            text = "No Photo"
            
            # Try to use a default font
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            
            # Calculate text position to center it
            text_width, text_height = (50, 10)  # Approximate size
            position = ((width - text_width) // 2, (height - text_height) // 2)
            
            # Draw text
            draw.text(position, text, fill=(0, 0, 0), font=font)
            
            # Draw a border around the image
            draw.rectangle([(0, 0), (width-1, height-1)], outline=(0, 0, 0), width=2)
            
            # Save the image
            filename = f"citizen_{citizen_id}_placeholder.jpg"
            placeholder_path = file_manager._get_file_path("photo", filename)
            img.save(placeholder_path, format="JPEG", quality=95)
            
            # Return relative path
            relative_path = str(placeholder_path.relative_to(file_manager.base_dir))
            logger.info(f"Created placeholder photo at {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Error creating placeholder photo: {str(e)}")
            return None
    
    def _generate_front_image(self, license_data: Dict[str, Any], 
                            citizen_data: Dict[str, Any], 
                            photo_path: str) -> bytes:
        """Generate front side image with improved photo handling"""
        try:
            photo_base64 = None
            
            if photo_path and file_manager.file_exists(photo_path):
                # Read processed photo
                logger.info(f"Reading photo from path: {photo_path}")
                photo_content = file_manager.get_file_content(photo_path)
                
                if photo_content:
                    photo_base64 = base64.b64encode(photo_content).decode('utf-8')
                    logger.info(f"Successfully converted photo to base64 (length: {len(photo_base64)})")
                else:
                    logger.warning(f"Photo file at {photo_path} is empty or could not be read")
            else:
                logger.warning(f"Photo path {photo_path} does not exist or is invalid")
            
            # Generate using SA generator (will handle missing photo gracefully)
            logger.info("Generating front license image with SA generator")
            front_image_base64 = self.sa_generator.generate_front(license_data, photo_base64)
            
            if not front_image_base64:
                raise ValueError("SA generator returned empty image")
            
            logger.info(f"Successfully generated front image (base64 length: {len(front_image_base64)})")
            
            # Convert back to bytes
            image_bytes = base64.b64decode(front_image_base64)
            logger.info(f"Converted to bytes (length: {len(image_bytes)})")
            
            return image_bytes
            
        except Exception as e:
            logger.error(f"Error generating front image: {str(e)}")
            # Create a simple error image as fallback
            from PIL import Image, ImageDraw, ImageFont
            
            error_img = Image.new('RGB', (CARD_W_PX, CARD_H_PX), (255, 255, 255))
            draw = ImageDraw.Draw(error_img)
            draw.text((CARD_W_PX//2, CARD_H_PX//2), "ERROR GENERATING\nLICENSE IMAGE", 
                     fill=(255, 0, 0), anchor="mm")
            
            buffer = io.BytesIO()
            error_img.save(buffer, format="PNG")
            return buffer.getvalue()
    
    def _generate_back_image(self, license_data: Dict[str, Any], 
                           citizen_data: Dict[str, Any]) -> bytes:
        """Generate back side image with improved error handling"""
        try:
            logger.info("Generating back license image with SA generator")
            back_image_base64 = self.sa_generator.generate_back(license_data)
            
            if not back_image_base64:
                raise ValueError("SA generator returned empty back image")
            
            logger.info(f"Successfully generated back image (base64 length: {len(back_image_base64)})")
            
            # Convert back to bytes
            image_bytes = base64.b64decode(back_image_base64)
            logger.info(f"Converted back image to bytes (length: {len(image_bytes)})")
            
            return image_bytes
            
        except Exception as e:
            logger.error(f"Error generating back image: {str(e)}")
            # Create a simple error image as fallback
            from PIL import Image, ImageDraw
            
            error_img = Image.new('RGB', (CARD_W_PX, CARD_H_PX), (255, 255, 255))
            draw = ImageDraw.Draw(error_img)
            draw.text((CARD_W_PX//2, CARD_H_PX//2), "ERROR GENERATING\nBACK IMAGE", 
                     fill=(255, 0, 0), anchor="mm")
            
            buffer = io.BytesIO()
            error_img.save(buffer, format="PNG")
            return buffer.getvalue()
    
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
        
        # Create a unique temporary file path instead of using BytesIO directly
        temp_img_path = file_manager._get_file_path("temp", f"temp_img_{uuid.uuid4()}.png")
        with open(temp_img_path, 'wb') as f:
            f.write(image_bytes)
        
        # Add image to PDF using the file path
        c.drawImage(
            str(temp_img_path), 0, 0,
            width=page_width, height=page_height,
            preserveAspectRatio=True
        )
        
        c.save()
        
        # Clean up temporary file
        try:
            import os
            os.unlink(temp_img_path)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {temp_img_path}: {str(e)}")
        
        return pdf_buffer.getvalue()
    
    def _generate_combined_pdf_with_watermark(self, front_bytes: bytes, back_bytes: bytes, 
                                              watermark_bytes: bytes, license_data: Dict[str, Any]) -> bytes:
        """
        Generate combined PDF with both front and back and watermark
        
        Args:
            front_bytes: Front image bytes
            back_bytes: Back image bytes
            watermark_bytes: Watermark image bytes
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
        
        # Create temporary files for the images
        front_temp_path = file_manager._get_file_path("temp", f"temp_front_{uuid.uuid4()}.png")
        back_temp_path = file_manager._get_file_path("temp", f"temp_back_{uuid.uuid4()}.png")
        watermark_temp_path = file_manager._get_file_path("temp", f"temp_watermark_{uuid.uuid4()}.png")
        
        with open(front_temp_path, 'wb') as f:
            f.write(front_bytes)
            
        with open(back_temp_path, 'wb') as f:
            f.write(back_bytes)
            
        with open(watermark_temp_path, 'wb') as f:
            f.write(watermark_bytes)
        
        # Front page using file path
        c.drawImage(
            str(front_temp_path), 0, 0,
            width=page_width, height=page_height,
            preserveAspectRatio=True
        )
        c.showPage()
        
        # Back page using file path
        c.drawImage(
            str(back_temp_path), 0, 0,
            width=page_width, height=page_height,
            preserveAspectRatio=True
        )
        c.showPage()
        
        # Watermark page using file path
        c.drawImage(
            str(watermark_temp_path), 0, 0,
            width=page_width, height=page_height,
            preserveAspectRatio=True
        )
        
        c.save()
        
        # Clean up temporary files
        try:
            import os
            os.unlink(front_temp_path)
            os.unlink(back_temp_path)
            os.unlink(watermark_temp_path)
        except Exception as e:
            logger.warning(f"Failed to delete temporary files: {str(e)}")
        
        return pdf_buffer.getvalue()
    
    def _generate_watermark_image(self, license_data: Dict[str, Any]) -> bytes:
        """Generate watermark image as separate file"""
        try:
            logger.info("Generating watermark image with SA generator")
            watermark_base64 = self.sa_generator.generate_watermark_template(CARD_W_PX, CARD_H_PX, "SOUTH AFRICA")
            
            if not watermark_base64:
                raise ValueError("SA generator returned empty watermark image")
            
            logger.info(f"Successfully generated watermark image (base64 length: {len(watermark_base64)})")
            
            # Convert back to bytes
            image_bytes = base64.b64decode(watermark_base64)
            logger.info(f"Converted watermark image to bytes (length: {len(image_bytes)})")
            
            return image_bytes
            
        except Exception as e:
            logger.error(f"Error generating watermark image: {str(e)}")
            # Create a simple fallback watermark image
            from PIL import Image, ImageDraw
            
            watermark_img = Image.new('RGB', (CARD_W_PX, CARD_H_PX), (255, 255, 255))
            draw = ImageDraw.Draw(watermark_img)
            
            # Simple diagonal text pattern
            text = "SOUTH AFRICA"
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            # Draw diagonal pattern
            for y in range(0, CARD_H_PX, 100):
                for x in range(0, CARD_W_PX, 200):
                    draw.text((x, y), text, fill=(200, 200, 200), font=font)
            
            buffer = io.BytesIO()
            watermark_img.save(buffer, format="PNG")
            return buffer.getvalue()
    
    def _files_exist(self, license_id: int) -> bool:
        """Check if all license files exist"""
        required_files = [
            f"licenses/license_{license_id}_front.png",
            f"licenses/license_{license_id}_back.png",
            f"licenses/license_{license_id}_watermark.png",
            f"licenses/license_{license_id}_combined.pdf"
        ]
        
        return all(file_manager.file_exists(path) for path in required_files)
    
    def _get_existing_file_info(self, license_id: int) -> Dict[str, str]:
        """Get information about existing files"""
        paths = {
            "front_image_path": f"licenses/license_{license_id}_front.png",
            "back_image_path": f"licenses/license_{license_id}_back.png",
            "watermark_image_path": f"licenses/license_{license_id}_watermark.png",
            "front_pdf_path": f"licenses/license_{license_id}_front.pdf",
            "back_pdf_path": f"licenses/license_{license_id}_back.pdf",
            "watermark_pdf_path": f"licenses/license_{license_id}_watermark.pdf",
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
            
            return original_path, processed_path
        except Exception as e:
            logger.error(f"Error updating citizen photo: {str(e)}")
            raise

# Create a singleton instance
production_generator = ProductionLicenseGenerator() 