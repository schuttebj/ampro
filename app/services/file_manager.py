import os
import io
import hashlib
import shutil
from datetime import datetime, timedelta
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
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Ensured directory exists: {directory}")
            except Exception as e:
                logger.error(f"Error creating directory {directory}: {str(e)}")
                
        # Add a .gitkeep file to keep the directories in git
        for directory in [self.licenses_dir, self.photos_dir, self.temp_dir]:
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                try:
                    with open(gitkeep, 'w') as f:
                        f.write("")
                    logger.info(f"Created .gitkeep in {directory}")
                except Exception as e:
                    logger.error(f"Error creating .gitkeep in {directory}: {str(e)}")
    
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
    
    def store_uploaded_file(self, content: bytes, filename: str, category: str = "photo") -> Tuple[str, str]:
        """
        Store uploaded file content and return paths
        
        Args:
            content: File content as bytes
            filename: Original filename (used for extension)
            category: Storage category (photo, temp, etc.)
        
        Returns:
            Tuple of (relative_path, file_url)
        """
        try:
            # Generate content hash for deduplication
            content_hash = self._generate_file_hash(content)
            
            # Get file extension
            file_extension = Path(filename).suffix.lower()
            if not file_extension:
                file_extension = ".jpg"  # Default extension
            
            # Generate unique filename with hash
            unique_filename = f"upload_{content_hash}{file_extension}"
            
            # Get file path
            file_path = self._get_file_path(category, unique_filename)
            
            # Check if file already exists (deduplication)
            if file_path.exists():
                logger.info(f"File already exists, reusing: {unique_filename}")
            else:
                # Write new file
                with open(file_path, 'wb') as f:
                    f.write(content)
                logger.info(f"Stored new file: {unique_filename}")
            
            # Return relative path and URL
            relative_path = str(file_path.relative_to(self.base_dir))
            file_url = self.get_file_url(relative_path)
            
            return relative_path, file_url
            
        except Exception as e:
            logger.error(f"Error storing uploaded file: {str(e)}")
            raise
    
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
        
        logger.info(f"Downloading/storing photo for citizen {citizen_id} from URL: {photo_url}")
        
        try:
            # Check if this is a local file URL (either static or API serve endpoint)
            if photo_url.startswith('/static/storage/'):
                # This is a direct path to our storage
                file_path = photo_url.replace('/static/storage/', '')
                full_path = self.base_dir / file_path
                
                if not full_path.exists():
                    logger.warning(f"File not found at {full_path}")
                    raise FileNotFoundError(f"Local file not found: {file_path}")
                
                # Get file bytes
                with open(full_path, 'rb') as f:
                    photo_bytes = f.read()
                    
                logger.info(f"Got photo from static storage: {file_path}")
                
            elif photo_url.startswith('/api/v1/files/serve/'):
                # This is a path via our API serve endpoint
                file_path = photo_url.replace('/api/v1/files/serve/', '')
                logger.info(f"Checking API serve path: {self.base_dir / file_path}")
                
                # Check if file exists in storage
                full_path = self.base_dir / file_path
                if full_path.exists():
                    # Get file bytes
                    with open(full_path, 'rb') as f:
                        photo_bytes = f.read()
                    logger.info(f"Got photo from API serve endpoint: {file_path}")
                else:
                    # File doesn't exist in storage, try alternative path (without photos/ prefix)
                    file_name = os.path.basename(file_path)
                    alt_path = self.base_dir / "photos" / file_name
                    logger.info(f"File not found at {full_path}, trying alternative path: {alt_path}")
                    
                    if alt_path.exists():
                        # Get file bytes
                        with open(alt_path, 'rb') as f:
                            photo_bytes = f.read()
                        logger.info(f"Got photo from alternative path: {alt_path}")
                    else:
                        # Search for any existing photos for this citizen
                        existing_photos = list(self.photos_dir.glob(f"citizen_{citizen_id}_*"))
                        logger.info(f"Searching for existing citizen photos: found {len(existing_photos)} files")
                        
                        if existing_photos:
                            # Use the most recent photo
                            latest_photo = max(existing_photos, key=lambda p: p.stat().st_mtime)
                            with open(latest_photo, 'rb') as f:
                                photo_bytes = f.read()
                            logger.info(f"Using existing citizen photo: {latest_photo}")
                        else:
                            # Last resort: attempt to create an empty placeholder
                            try:
                                # Create photos directory if it doesn't exist
                                self.photos_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Generate a blank image
                                from PIL import Image, ImageDraw
                                img = Image.new('RGB', (300, 400), color=(240, 240, 240))
                                draw = ImageDraw.Draw(img)
                                # Draw a black border
                                draw.rectangle([(0, 0), (299, 399)], outline=(0, 0, 0), width=2)
                                
                                # Save to a BytesIO object
                                import io
                                img_bytes = io.BytesIO()
                                img.save(img_bytes, format='PNG')
                                photo_bytes = img_bytes.getvalue()
                                logger.info(f"Created blank placeholder image")
                            except Exception as e:
                                logger.error(f"Error creating placeholder: {str(e)}")
                                raise FileNotFoundError(f"Local file not found: {file_path}")
            
            elif photo_url.startswith(('http://', 'https://')):
                # External URL - download the photo
                import requests
                response = requests.get(photo_url, timeout=10)
                response.raise_for_status()  # Raise exception for HTTP errors
                photo_bytes = response.content
                logger.info(f"Downloaded photo from external URL: {photo_url}")
                
            else:
                # Try as a direct relative path
                file_path = photo_url.lstrip('/')
                full_path = self.base_dir / file_path
                
                if full_path.exists():
                    # Get file bytes
                    with open(full_path, 'rb') as f:
                        photo_bytes = f.read()
                    logger.info(f"Got photo from direct path: {file_path}")
                else:
                    # Try another location by checking photos directory directly
                    filename = os.path.basename(file_path)
                    alt_path = self.photos_dir / filename
                    if alt_path.exists():
                        with open(alt_path, 'rb') as f:
                            photo_bytes = f.read()
                        logger.info(f"Got photo from photos directory: {filename}")
                    else:
                        # Last resort: just like above, create a placeholder
                        try:
                            # Create photos directory if it doesn't exist
                            self.photos_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Generate a blank image
                            from PIL import Image, ImageDraw
                            img = Image.new('RGB', (300, 400), color=(240, 240, 240))
                            draw = ImageDraw.Draw(img)
                            # Draw a black border
                            draw.rectangle([(0, 0), (299, 399)], outline=(0, 0, 0), width=2)
                            
                            # Save to a BytesIO object
                            import io
                            img_bytes = io.BytesIO()
                            img.save(img_bytes, format='PNG')
                            photo_bytes = img_bytes.getvalue()
                            logger.info(f"Created blank placeholder image for {file_path}")
                        except Exception as e:
                            logger.error(f"Error creating placeholder: {str(e)}")
                            raise FileNotFoundError(f"Local file not found: {file_path}")
            
            # Generate unique filenames for storing
            original_filename = f"citizen_{citizen_id}_original_{self._generate_file_hash(photo_bytes)}.jpg"
            processed_filename = f"citizen_{citizen_id}_processed_{self._generate_file_hash(photo_bytes)}.jpg"
            
            # Get paths
            original_path = self._get_file_path("photo", original_filename)
            processed_path = self._get_file_path("photo", processed_filename)
            
            # Ensure the directories exist
            original_path.parent.mkdir(parents=True, exist_ok=True)
            processed_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save original photo
            with open(original_path, 'wb') as f:
                f.write(photo_bytes)
            
            # Process photo (resize, apply ISO specs)
            try:
                self._process_photo(photo_bytes, processed_path)
            except Exception as e:
                logger.error(f"Error processing photo: {str(e)}")
                # If processing fails, just use the original as processed
                with open(processed_path, 'wb') as f:
                    f.write(photo_bytes)
            
            # Return relative paths
            relative_original = str(original_path.relative_to(self.base_dir))
            relative_processed = str(processed_path.relative_to(self.base_dir))
            
            return relative_original, relative_processed
            
        except Exception as e:
            logger.error(f"Error downloading/storing photo: {str(e)}")
            raise
    
    def _process_photo_for_iso_compliance(self, input_path: Path, output_path: Path):
        """
        Process photo to meet ISO 18013 specifications
        
        Args:
            input_path: Path to input image
            output_path: Path to save processed image
        """
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate aspect ratio
                target_ratio = ISO_PHOTO_SPECS["width_px"] / ISO_PHOTO_SPECS["height_px"]
                current_ratio = img.width / img.height
                
                # Crop to correct aspect ratio
                if current_ratio > target_ratio:
                    # Image is too wide, crop width
                    new_width = int(img.height * target_ratio)
                    left = (img.width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, img.height))
                elif current_ratio < target_ratio:
                    # Image is too tall, crop height
                    new_height = int(img.width / target_ratio)
                    top = (img.height - new_height) // 2
                    img = img.crop((0, top, img.width, top + new_height))
                
                # Resize to exact ISO specifications
                img = img.resize(
                    (ISO_PHOTO_SPECS["width_px"], ISO_PHOTO_SPECS["height_px"]),
                    Image.Resampling.LANCZOS
                )
                
                # Apply subtle sharpening
                img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
                
                # Ensure white background if image has transparency
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, ISO_PHOTO_SPECS["background_color"])
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img, mask=img.split()[-1])
                    img = background
                
                # Save with high quality
                img.save(
                    output_path,
                    format=ISO_PHOTO_SPECS["format"],
                    quality=ISO_PHOTO_SPECS["quality"],
                    dpi=(ISO_PHOTO_SPECS["dpi"], ISO_PHOTO_SPECS["dpi"])
                )
        except Exception as e:
            logger.error(f"Error processing photo for ISO compliance: {str(e)}")
            raise
    
    def _process_photo(self, photo_bytes: bytes, output_path: Path) -> None:
        """
        Process photo to meet ISO standards
        
        Args:
            photo_bytes: Raw photo bytes
            output_path: Path to save processed photo
        """
        try:
            from PIL import Image, ImageOps
            import io
            
            # Open image from bytes
            img = Image.open(io.BytesIO(photo_bytes))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Determine target dimensions for ISO ID photo
            # Standard ID photo is 35mm x 45mm at 300 DPI
            target_width = 413   # 35mm at 300 DPI
            target_height = 531  # 45mm at 300 DPI
            
            # Resize maintaining aspect ratio
            img.thumbnail((target_width, target_height), Image.LANCZOS)
            
            # Create a blank canvas with correct dimensions and paste the image centered
            canvas = Image.new('RGB', (target_width, target_height), (255, 255, 255))
            
            # Calculate position to center the image
            x = (target_width - img.width) // 2
            y = (target_height - img.height) // 2
            
            # Paste image on canvas
            canvas.paste(img, (x, y))
            
            # Apply any final adjustments
            canvas = ImageOps.autocontrast(canvas)
            
            # Save as high-quality JPEG
            canvas.save(output_path, 'JPEG', quality=95)
            logger.info(f"Processed photo saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error processing photo: {str(e)}")
            raise
    
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
    
    def cleanup_citizen_files(self, citizen_id: int, keep_latest: bool = True):
        """
        Clean up all files for a citizen, optionally keeping the latest ones
        
        Args:
            citizen_id: Citizen ID
            keep_latest: Whether to keep the most recent files
        """
        try:
            photo_pattern = f"citizen_{citizen_id}_*"
            photo_files = list(self.photos_dir.glob(photo_pattern))
            
            if keep_latest and photo_files:
                # Sort by modification time and keep the latest
                photo_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                files_to_delete = photo_files[2:]  # Keep latest original and processed
            else:
                files_to_delete = photo_files
            
            for photo_file in files_to_delete:
                try:
                    photo_file.unlink()
                    logger.info(f"Cleaned up citizen file: {photo_file}")
                except Exception as e:
                    logger.error(f"Error cleaning up {photo_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error during citizen file cleanup: {str(e)}")
    
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
        # Check if this is a photo file
        if relative_path.startswith('photos/') or '/photos/' in relative_path:
            # Extract filename for public photo endpoint
            filename = Path(relative_path).name
            return f"/api/v1/files/public/photos/{filename}"
        
        # For non-photo files, use the authenticated endpoint
        return f"/api/v1/files/serve/{relative_path}"
    
    def file_exists(self, file_path: str, force_create_directories: bool = False) -> bool:
        """
        Check if a file exists in storage
        
        Args:
            file_path: Relative path to file
            force_create_directories: If True, create any missing parent directories
            
        Returns:
            True if file exists, False otherwise
        """
        if not file_path:
            return False
            
        # Check if this is a relative or absolute path
        if os.path.isabs(file_path):
            # This is an absolute path, check if it exists directly
            exists = os.path.isfile(file_path)
            if exists:
                return True
                
            # Convert to a path relative to our storage base if possible
            try:
                full_path = Path(file_path)
                # Check if this path is under our storage directory
                if str(self.base_dir) in str(full_path):
                    # Convert to relative path
                    rel_path = str(full_path.relative_to(self.base_dir))
                    # Continue with the relative path
                    file_path = rel_path
                else:
                    # Not in our storage directory
                    return False
            except (ValueError, TypeError):
                # Can't convert to relative path
                return False
        
        # Handle relative paths
        full_path = self.base_dir / file_path
        exists = full_path.is_file()
        
        # Also try with no leading slash
        if not exists and file_path.startswith('/'):
            alt_path = self.base_dir / file_path.lstrip('/')
            exists = alt_path.is_file()
            if exists:
                full_path = alt_path
        
        # If file doesn't exist but force_create_directories is True, create the directories
        if not exists and force_create_directories:
            try:
                # Create parent directories
                full_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path.parent}")
            except Exception as e:
                logger.error(f"Error creating directories for {file_path}: {str(e)}")
        
        return exists
    
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
            older_than_hours: Files older than this will be deleted
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            
            for temp_file in self.temp_dir.glob("*"):
                if temp_file.is_file():
                    file_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        try:
                            temp_file.unlink()
                            logger.info(f"Cleaned up temp file: {temp_file}")
                        except Exception as e:
                            logger.error(f"Error cleaning up {temp_file}: {str(e)}")
                            
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {str(e)}")
    
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