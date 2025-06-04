import base64
import io
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import logging
import time

from app.services.file_manager import file_manager
from app import crud
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class WebcamService:
    """
    Service for handling webcam photo capture functionality.
    This service provides both mock implementation for testing and real webcam integration.
    """
    
    def __init__(self):
        self.storage_path = Path("app/static/storage/photos")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.use_real_webcam = True  # Enable real webcam integration by default
    
    def detect_available_webcams(self) -> List[Dict[str, Any]]:
        """
        Detect available webcams on the system.
        Returns a list of webcam devices with their capabilities.
        """
        if not self.use_real_webcam:
            # Mock webcam detection for testing
            return [
                {
                    "device_id": "0",
                    "name": "Default Camera",
                    "manufacturer": "Virtual",
                    "capabilities": {
                        "max_resolution": "1920x1080",
                        "formats": ["jpeg", "png"],
                        "fps": 30
                    }
                }
            ]
        
        # Real webcam detection would go here
        # This would use OpenCV or similar library
        try:
            import cv2
            webcams = []
            
            # Try to detect webcams
            for i in range(10):  # Check first 10 camera indices
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    
                    webcams.append({
                        "device_id": str(i),
                        "name": f"Camera {i}",
                        "manufacturer": "Unknown",
                        "capabilities": {
                            "max_resolution": f"{width}x{height}",
                            "formats": ["jpeg", "png"],
                            "fps": fps if fps > 0 else 30
                        }
                    })
                    cap.release()
                else:
                    break
            
            return webcams
            
        except ImportError:
            logger.warning("OpenCV not available, using mock webcam detection")
            # Fall back to mock webcam detection instead of calling self recursively
            return [
                {
                    "device_id": "0",
                    "name": "Default Camera",
                    "manufacturer": "Virtual",
                    "capabilities": {
                        "max_resolution": "1920x1080",
                        "formats": ["jpeg", "png"],
                        "fps": 30
                    }
                }
            ]
        except Exception as e:
            logger.error(f"Error detecting webcams: {str(e)}")
            return []
    
    def capture_photo(
        self,
        hardware_id: int,
        citizen_id: int,
        quality: str = "high",
        format: str = "jpeg",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Capture a photo using the specified webcam hardware.
        
        Args:
            hardware_id: ID of the webcam hardware
            citizen_id: ID of the citizen
            quality: Photo quality (high, medium, low)
            format: Photo format (jpeg, png)
            metadata: Additional metadata
        
        Returns:
            Dictionary with capture result
        """
        try:
            logger.info(f"Attempting photo capture for citizen {citizen_id} using hardware {hardware_id}")
            
            if self.use_real_webcam:
                # Real webcam capture
                result = self._capture_real_photo(
                    hardware_id=hardware_id,
                    citizen_id=citizen_id,
                    quality=quality,
                    format=format,
                    metadata=metadata
                )
            else:
                # Mock webcam capture for testing
                result = self._simulate_photo_capture(
                    hardware_id=hardware_id,
                    citizen_id=citizen_id,
                    quality=quality,
                    format=format,
                    metadata=metadata
                )
            
            if result["success"]:
                # Process the captured photo
                processed_result = self._process_captured_photo(
                    photo_data=result["photo_data"],
                    citizen_id=citizen_id,
                    quality=quality,
                    format=format
                )
                
                return {
                    "success": True,
                    "photo_url": processed_result["photo_url"],
                    "stored_photo_path": processed_result["stored_photo_path"],
                    "processed_photo_path": processed_result["processed_photo_path"],
                    "metadata": {
                        "hardware_id": hardware_id,
                        "citizen_id": citizen_id,
                        "quality": quality,
                        "format": format,
                        "capture_time": datetime.now().isoformat(),
                        "original_metadata": metadata,
                        "capture_method": "real_webcam" if self.use_real_webcam else "simulated"
                    }
                }
            else:
                return {
                    "success": False,
                    "error_message": result.get("error_message", "Photo capture failed")
                }
                
        except Exception as e:
            logger.error(f"Error during photo capture: {str(e)}")
            return {
                "success": False,
                "error_message": f"Capture error: {str(e)}"
            }
    
    def _capture_real_photo(
        self,
        hardware_id: int,
        citizen_id: int,
        quality: str,
        format: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Capture photo using real webcam hardware.
        """
        try:
            import cv2
            
            # Get hardware device information from database
            with SessionLocal() as db:
                hardware = crud.hardware.get(db, id=hardware_id)
                if not hardware:
                    return {
                        "success": False,
                        "error_message": f"Hardware device {hardware_id} not found"
                    }
                
                # Use device_id from hardware record, default to 0 if not set
                device_index = int(hardware.device_id) if hardware.device_id else 0
            
            logger.info(f"Attempting to capture photo using device index {device_index}")
            
            cap = cv2.VideoCapture(device_index)
            if not cap.isOpened():
                return {
                    "success": False,
                    "error_message": f"Could not open webcam device {device_index}. Please check if the webcam is connected and not being used by another application."
                }
            
            # Set quality parameters
            if quality == "high":
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            elif quality == "medium":
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            else:  # low
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Allow camera to warm up
            time.sleep(0.5)
            
            # Capture frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return {
                    "success": False,
                    "error_message": "Failed to capture frame from webcam. Please ensure the camera is properly connected."
                }
            
            # Convert frame to bytes
            if format.lower() == "png":
                success, encoded_img = cv2.imencode('.png', frame)
            else:
                success, encoded_img = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            if not success:
                return {
                    "success": False,
                    "error_message": "Failed to encode captured frame"
                }
            
            photo_data = encoded_img.tobytes()
            
            logger.info(f"Successfully captured photo from device {device_index}, size: {len(photo_data)} bytes")
            
            return {
                "success": True,
                "photo_data": photo_data,
                "format": format,
                "quality": quality,
                "capture_info": {
                    "device_index": device_index,
                    "frame_width": frame.shape[1],
                    "frame_height": frame.shape[0]
                }
            }
            
        except ImportError:
            logger.error("OpenCV not available for real webcam capture")
            return {
                "success": False,
                "error_message": "OpenCV not available for webcam capture. Please install opencv-python."
            }
        except Exception as e:
            logger.error(f"Error in real photo capture: {str(e)}")
            return {
                "success": False,
                "error_message": f"Real capture error: {str(e)}"
            }
    
    def _simulate_photo_capture(
        self,
        hardware_id: int,
        citizen_id: int,
        quality: str,
        format: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulate photo capture for testing purposes.
        In production, this would be replaced with actual webcam integration.
        """
        # This creates a mock photo capture
        # In real implementation, this would:
        # 1. Connect to the webcam device using hardware_id
        # 2. Configure capture settings based on quality and format
        # 3. Capture the actual photo
        # 4. Return the raw photo data
        
        # For simulation, we'll create a placeholder image
        try:
            # Generate a simple colored rectangle as placeholder
            from PIL import Image, ImageDraw, ImageFont
            
            # Set dimensions based on quality
            if quality == "high":
                width, height = 1920, 1080
            elif quality == "medium":
                width, height = 1280, 720
            else:  # low
                width, height = 640, 480
            
            # Create image
            img = Image.new('RGB', (width, height), color='lightblue')
            draw = ImageDraw.Draw(img)
            
            # Add some text to indicate it's a captured photo
            try:
                # Use default font
                font = ImageFont.load_default()
            except:
                font = None
            
            text = f"Citizen {citizen_id}\nCaptured: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nCamera: {hardware_id}\nQuality: {quality}"
            
            # Calculate text position (center)
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width = len(text) * 6  # Rough estimate
                text_height = 20
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG' if format.lower() == 'jpeg' else 'PNG')
            img_bytes.seek(0)
            
            return {
                "success": True,
                "photo_data": img_bytes.getvalue(),
                "format": format,
                "quality": quality
            }
            
        except Exception as e:
            logger.error(f"Error in photo simulation: {str(e)}")
            return {
                "success": False,
                "error_message": f"Simulation error: {str(e)}"
            }
    
    def _process_captured_photo(
        self,
        photo_data: bytes,
        citizen_id: int,
        quality: str,
        format: str
    ) -> Dict[str, Any]:
        """
        Process the captured photo and store it using the file manager.
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = str(uuid.uuid4())[:8]
            
            # Create temporary file-like object
            photo_file = io.BytesIO(photo_data)
            
            # Use file manager to store and process the photo
            original_path, processed_path = file_manager.download_and_store_photo(
                photo_url=None,  # No URL since we have raw data
                citizen_id=citizen_id,
                photo_data=photo_data  # Pass raw data directly
            )
            
            return {
                "photo_url": f"/api/v1/files/photos/citizen_{citizen_id}_processed_{file_hash}.jpg",
                "stored_photo_path": original_path,
                "processed_photo_path": processed_path
            }
            
        except Exception as e:
            logger.error(f"Error processing captured photo: {str(e)}")
            raise
    
    def test_webcam(self, hardware_id: int) -> Dict[str, Any]:
        """
        Test webcam functionality.
        """
        try:
            # In real implementation, this would:
            # 1. Try to connect to the webcam
            # 2. Capture a test frame
            # 3. Return connection status
            
            logger.info(f"Testing webcam hardware {hardware_id}")
            
            # Mock test - always return success for simulation
            return {
                "success": True,
                "hardware_id": hardware_id,
                "status": "online",
                "capabilities": {
                    "max_resolution": "1920x1080",
                    "formats": ["jpeg", "png"],
                    "features": ["auto_focus", "auto_exposure"]
                },
                "test_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error testing webcam {hardware_id}: {str(e)}")
            return {
                "success": False,
                "hardware_id": hardware_id,
                "status": "error",
                "error_message": str(e),
                "test_time": datetime.now().isoformat()
            }
    
    def get_webcam_settings(self, hardware_id: int) -> Dict[str, Any]:
        """
        Get webcam settings and capabilities.
        """
        # Mock settings - in real implementation, this would query the actual hardware
        return {
            "hardware_id": hardware_id,
            "resolution_options": [
                {"width": 1920, "height": 1080, "name": "Full HD"},
                {"width": 1280, "height": 720, "name": "HD"},
                {"width": 640, "height": 480, "name": "Standard"}
            ],
            "quality_options": ["high", "medium", "low"],
            "format_options": ["jpeg", "png"],
            "features": {
                "auto_focus": True,
                "auto_exposure": True,
                "flash": False,
                "zoom": True
            },
            "current_settings": {
                "resolution": {"width": 1920, "height": 1080},
                "quality": "high",
                "format": "jpeg",
                "auto_focus": True,
                "auto_exposure": True
            }
        }
    
    def enable_real_webcam(self, enable: bool = True):
        """
        Enable or disable real webcam integration.
        When disabled, uses mock/simulation mode.
        """
        self.use_real_webcam = enable
        logger.info(f"Real webcam mode {'enabled' if enable else 'disabled'}")
    
    def get_webcam_status(self, hardware_id: int) -> Dict[str, Any]:
        """
        Get the current status of a webcam.
        """
        if self.use_real_webcam:
            try:
                import cv2
                device_index = 0  # Map hardware_id to device in real implementation
                
                cap = cv2.VideoCapture(device_index)
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    cap.release()
                    
                    return {
                        "hardware_id": hardware_id,
                        "status": "ACTIVE",
                        "device_info": {
                            "device_index": device_index,
                            "resolution": f"{width}x{height}",
                            "fps": fps
                        },
                        "last_checked": datetime.now().isoformat()
                    }
                else:
                    return {
                        "hardware_id": hardware_id,
                        "status": "OFFLINE",
                        "error": "Could not open webcam device",
                        "last_checked": datetime.now().isoformat()
                    }
                    
            except ImportError:
                return {
                    "hardware_id": hardware_id,
                    "status": "ERROR",
                    "error": "OpenCV not available",
                    "last_checked": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "hardware_id": hardware_id,
                    "status": "ERROR",
                    "error": str(e),
                    "last_checked": datetime.now().isoformat()
                }
        else:
            # Mock status
            return {
                "hardware_id": hardware_id,
                "status": "ACTIVE",
                "device_info": {
                    "simulated": True,
                    "resolution": "1920x1080",
                    "fps": 30
                },
                "last_checked": datetime.now().isoformat()
            }


# Global instance
webcam_service = WebcamService() 