import os
import io
import hashlib
import shutil
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import requests
from PIL import Image, ImageOps, ImageFilter
import logging

# Configure logging
logger = logging.getLogger(__name__)

# File storage configuration
STORAGE_BASE_DIR = os.environ.get("AMPRO_STORAGE_DIR", "app/static/storage")
LICENSES_DIR = "licenses"
PHOTOS_DIR = "photos"
TEMP_DIR = "temp"

# ISO specifications for photo processing
ISO_PHOTO_SPECS = {
    "width_mm": 18,
    "height_mm": 22,
    "width_px": 213,  # 18mm at 300 DPI
    "height_px": 260,  # 22mm at 300 DPI
    "dpi": 300,
    "format": "JPEG",
    "quality": 95,
    "background_color": (255, 255, 255),  # White background
}

class FileManager:
    """Handles all file operations for the AMPRO license system"""
    
    def __init__(self):
        self.base_dir = Path(STORAGE_BASE_DIR)
        self.licenses_dir = self.base_dir / LICENSES_DIR
        self.photos_dir = self.base_dir / PHOTOS_DIR
        self.temp_dir = self.base_dir / TEMP_DIR
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.base_dir, self.licenses_dir, self.photos_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _generate_file_hash(self, content: bytes) -> str:
        """Generate SHA256 hash for file content"""
        return hashlib.sha256(content).hexdigest()
    
    def _get_file_path(self, category: str, filename: str) -> Path:
        """Get full file path for a given category and filename"""
        if category == "license":
            return self.licenses_dir / filename
        elif category == "photo":
            return self.photos_dir / filename
        elif category == "temp":
            return self.temp_dir / filename
        else:
            raise ValueError(f"Unknown file category: {category}")
    
    def save_license_file(self, license_id: int, file_type: str, content: bytes, 
                         extension: str = "png") -> str:
        """
        Save license file and return the relative path
        
        Args:
            license_id: License ID
            file_type: Type of file (front, back, combined, etc.)
            content: File content as bytes
            extension: File extension
        
        Returns:
            Relative path to the saved file
        """
        filename = f"license_{license_id}_{file_type}.{extension}"
        file_path = self._get_file_path("license", filename)
        
        # Remove old file if it exists
        if file_path.exists():
            file_path.unlink()
        
        # Write new file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Return relative path
        return str(file_path.relative_to(self.base_dir))
    
    def download_and_store_photo(self, photo_url: str, citizen_id: int) -> Tuple[str, str]:
        """
        Download photo from URL and store both original and processed versions
        
        Args:
            photo_url: URL of the photo to download
            citizen_id: Citizen ID for filename generation
        
        Returns:
            Tuple of (original_path, processed_path) relative to storage base
        """
        if not photo_url:
            raise ValueError("Photo URL is required")
        
        try:
            # Download the image
            response = requests.get(photo_url, timeout=30)
            response.raise_for_status()
            
            # Generate filename based on content hash
            content_hash = self._generate_file_hash(response.content)
            original_filename = f"citizen_{citizen_id}_original_{content_hash}.jpg"
            processed_filename = f"citizen_{citizen_id}_processed_{content_hash}.jpg"
            
            # Save original image
            original_path = self._get_file_path("photo", original_filename)
            with open(original_path, 'wb') as f:
                f.write(response.content)
            
            # Process image for ISO compliance
            processed_path = self._get_file_path("photo", processed_filename)
            self._process_photo_for_iso_compliance(original_path, processed_path)
            
            return (
                str(original_path.relative_to(self.base_dir)),
                str(processed_path.relative_to(self.base_dir))
            )
            
        except Exception as e:
            logger.error(f"Error downloading/storing photo: {str(e)}")
            raise
    
    def _process_photo_for_iso_compliance(self, input_path: Path, output_path: Path):
        """
        Process photo to meet ISO specifications for driver's license
        
        Args:
            input_path: Path to input image
            output_path: Path to save processed image
        """
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get target dimensions
            target_width = ISO_PHOTO_SPECS["width_px"]
            target_height = ISO_PHOTO_SPECS["height_px"]
            
            # Calculate crop dimensions to maintain aspect ratio
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                # Image is wider than target, crop width
                new_width = int(img.height * target_ratio)
                left = (img.width - new_width) // 2
                img = img.crop((left, 0, left + new_width, img.height))
            else:
                # Image is taller than target, crop height
                new_height = int(img.width / target_ratio)
                top = (img.height - new_height) // 2
                img = img.crop((0, top, img.width, top + new_height))
            
            # Resize to exact specifications
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Apply subtle sharpening for license photo quality
            img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=3))
            
            # Enhance contrast slightly
            img = ImageOps.autocontrast(img, cutoff=1)
            
            # Save with high quality
            img.save(
                output_path,
                format=ISO_PHOTO_SPECS["format"],
                quality=ISO_PHOTO_SPECS["quality"],
                dpi=(ISO_PHOTO_SPECS["dpi"], ISO_PHOTO_SPECS["dpi"])
            )
    
    def cleanup_old_files(self, citizen_id: int, exclude_paths: list = None):
        """
        Clean up old files for a citizen, excluding specified paths
        
        Args:
            citizen_id: Citizen ID
            exclude_paths: List of file paths to exclude from cleanup
        """
        exclude_paths = exclude_paths or []
        exclude_names = [Path(p).name for p in exclude_paths]
        
        # Clean up old photos
        photo_pattern = f"citizen_{citizen_id}_*"
        for photo_file in self.photos_dir.glob(photo_pattern):
            if photo_file.name not in exclude_names:
                try:
                    photo_file.unlink()
                    logger.info(f"Cleaned up old photo: {photo_file}")
                except Exception as e:
                    logger.error(f"Error cleaning up {photo_file}: {str(e)}")
    
    def cleanup_old_license_files(self, license_id: int, exclude_paths: list = None):
        """
        Clean up old license files, excluding specified paths
        
        Args:
            license_id: License ID
            exclude_paths: List of file paths to exclude from cleanup
        """
        exclude_paths = exclude_paths or []
        exclude_names = [Path(p).name for p in exclude_paths]
        
        # Clean up old license files
        license_pattern = f"license_{license_id}_*"
        for license_file in self.licenses_dir.glob(license_pattern):
            if license_file.name not in exclude_names:
                try:
                    license_file.unlink()
                    logger.info(f"Cleaned up old license file: {license_file}")
                except Exception as e:
                    logger.error(f"Error cleaning up {license_file}: {str(e)}")
    
    def get_file_url(self, relative_path: str) -> str:
        """
        Convert relative file path to accessible URL
        
        Args:
            relative_path: Relative path from storage base
        
        Returns:
            URL to access the file
        """
        return f"/static/storage/{relative_path}"
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists"""
        full_path = self.base_dir / relative_path
        return full_path.exists()
    
    def get_file_content(self, relative_path: str) -> bytes:
        """Get file content as bytes"""
        full_path = self.base_dir / relative_path
        with open(full_path, 'rb') as f:
            return f.read()
    
    def get_file_size(self, relative_path: str) -> int:
        """Get file size in bytes"""
        full_path = self.base_dir / relative_path
        return full_path.stat().st_size if full_path.exists() else 0
    
    def create_backup(self, relative_path: str) -> str:
        """
        Create a backup of a file
        
        Args:
            relative_path: Relative path to the file
        
        Returns:
            Backup file path
        """
        source_path = self.base_dir / relative_path
        backup_path = source_path.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        shutil.copy2(source_path, backup_path)
        return str(backup_path.relative_to(self.base_dir))
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Clean up temporary files older than specified hours
        
        Args:
            older_than_hours: Remove files older than this many hours
        """
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        
        for temp_file in self.temp_dir.glob("*"):
            if temp_file.is_file() and temp_file.stat().st_mtime < cutoff_time:
                try:
                    temp_file.unlink()
                    logger.info(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.error(f"Error cleaning up temp file {temp_file}: {str(e)}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "license_files": 0,
            "photo_files": 0,
            "temp_files": 0,
            "license_size_bytes": 0,
            "photo_size_bytes": 0,
            "temp_size_bytes": 0,
        }
        
        for directory, prefix in [(self.licenses_dir, "license"), 
                                  (self.photos_dir, "photo"), 
                                  (self.temp_dir, "temp")]:
            if directory.exists():
                for file_path in directory.glob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        stats["total_files"] += 1
                        stats["total_size_bytes"] += size
                        stats[f"{prefix}_files"] += 1
                        stats[f"{prefix}_size_bytes"] += size
        
        return stats


# Global file manager instance
file_manager = FileManager() 