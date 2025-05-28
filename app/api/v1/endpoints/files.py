from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
import shutil
import logging
from datetime import datetime
import mimetypes

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user, get_current_user_optional
from app.models.user import User
from app.services.file_manager import file_manager
from app.models.audit import ActionType, ResourceType
from app.crud import citizen as crud_citizen

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed file types and sizes
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload", response_model=Dict[str, str])
async def upload_file(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    file_type: str = Form("citizen_photo"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Upload a file and store it on the server.
    Returns file URL and path for database storage.
    """
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    try:
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        if not file_extension:
            file_extension = ".jpg"  # Default extension
        
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Determine storage category based on file type
        if file_type == "citizen_photo":
            category = "photo"
        else:
            category = "temp"
        
        # Save file using file manager
        file_path = file_manager._get_file_path(category, unique_filename)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Get relative path and URL
        relative_path = str(file_path.relative_to(file_manager.base_dir))
        file_url = file_manager.get_file_url(relative_path)
        
        # Log the upload
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.CREATE,
                "resource_type": ResourceType.FILE,
                "description": f"User {current_user.username} uploaded file: {file.filename} ({file_type})"
            }
        )
        
        logger.info(f"File uploaded successfully: {relative_path}")
        
        return {
            "file_url": file_url,
            "file_path": relative_path,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.delete("/delete", response_model=Dict[str, Any])
async def delete_file(
    *,
    db: Session = Depends(get_db),
    file_path: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a file from the server.
    """
    try:
        # Get full file path
        full_path = file_manager.base_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Delete the file
        full_path.unlink()
        
        # Log the deletion
        crud.audit_log.create(
            db,
            obj_in={
                "user_id": current_user.id,
                "action_type": ActionType.DELETE,
                "resource_type": ResourceType.FILE,
                "description": f"User {current_user.username} deleted file: {file_path}"
            }
        )
        
        logger.info(f"File deleted successfully: {file_path}")
        
        return {
            "success": True,
            "message": "File deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file: {str(e)}"
        )

@router.get("/serve/{file_path:path}")
async def serve_file(
    file_path: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Serve a file from storage (requires authentication).
    """
    try:
        # Security check - ensure path doesn't contain directory traversal
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )
        
        # Get full file path
        full_path = Path(file_manager.base_dir) / file_path
        
        # Check if file exists
        if not full_path.exists() or not full_path.is_file():
            # Try checking in the photos directory if not found
            alt_path = file_manager.photos_dir / Path(file_path).name
            if alt_path.exists() and alt_path.is_file():
                full_path = alt_path
            else:
                logger.warning(f"File not found: {full_path}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
        
        # Determine content type
        content_type = "application/octet-stream"
        file_ext = full_path.suffix.lower()
        if file_ext in ['.jpg', '.jpeg']:
            content_type = "image/jpeg"
        elif file_ext == '.png':
            content_type = "image/png"
        elif file_ext == '.pdf':
            content_type = "application/pdf"
        
        # Return file
        return FileResponse(
            path=str(full_path),
            media_type=content_type,
            filename=full_path.name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve file: {str(e)}"
        )

@router.get("/debug/{file_path:path}")
def debug_file_info(
    *,
    file_path: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Debug endpoint to check file existence and metadata
    """
    logger.info(f"Debug request for file: {file_path}")
    
    # First, check if file exists directly
    full_path = file_manager.base_dir / file_path
    exists_direct = full_path.exists()
    
    # Check if file exists using file_manager method
    exists_manager = file_manager.file_exists(file_path)
    
    # Check for files with the same name in photos directory
    filename = Path(file_path).name
    photos_path = file_manager.photos_dir / filename
    exists_in_photos = photos_path.exists()
    
    # Check for citizen files with similar pattern (if filename contains ID)
    citizen_id = None
    citizen_files = []
    parts = filename.split('_')
    if len(parts) > 1 and parts[0] == 'citizen':
        try:
            citizen_id = int(parts[1])
            citizen_files = list(file_manager.photos_dir.glob(f"citizen_{citizen_id}_*"))
            citizen_files = [str(p.relative_to(file_manager.base_dir)) for p in citizen_files]
        except (ValueError, IndexError):
            pass
    
    result = {
        "requested_path": file_path,
        "full_path": str(full_path),
        "exists_direct": exists_direct,
        "exists_manager": exists_manager,
        "filename": filename,
        "photos_path": str(photos_path),
        "exists_in_photos": exists_in_photos,
        "citizen_id": citizen_id,
        "citizen_files": citizen_files,
        "base_dir": str(file_manager.base_dir),
        "photos_dir": str(file_manager.photos_dir),
        "storage_dirs": {
            "exists": {
                "base": Path(file_manager.base_dir).exists(),
                "photos": Path(file_manager.photos_dir).exists(),
                "licenses": Path(file_manager.licenses_dir).exists(),
                "temp": Path(file_manager.temp_dir).exists()
            }
        }
    }
    
    # If file exists, add metadata
    if exists_direct:
        stat = full_path.stat()
        result.update({
            "size_bytes": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": full_path.is_file(),
            "is_dir": full_path.is_dir()
        })
    
    return result 

@router.post("/citizen/{citizen_id}/photo")
async def upload_citizen_photo(
    *,
    db: Session = Depends(get_db),
    citizen_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Upload a photo for a citizen.
    """
    # Check citizen exists
    citizen = crud_citizen.get(db, id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen not found"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Store photo
        relative_path, file_url = file_manager.store_uploaded_file(
            content=content,
            filename=f"citizen_{citizen_id}_{file.filename}",
            category="photo"
        )
        
        # Update citizen with photo URL
        citizen = crud_citizen.update(
            db,
            db_obj=citizen,
            obj_in={"photo_url": file_url}
        )
        
        logger.info(f"Photo uploaded for citizen {citizen_id}: {relative_path}")
        
        return {
            "success": True,
            "path": relative_path,
            "url": file_url,
            "citizen_id": citizen_id
        }
    except Exception as e:
        logger.error(f"Photo upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photo: {str(e)}"
        )

@router.get("/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get storage statistics.
    """
    try:
        stats = file_manager.get_storage_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}"
        )

@router.get("/public/photos/{filename}")
async def serve_public_photo(
    filename: str
) -> Any:
    """
    Serve photos publicly (no authentication required).
    This endpoint is specifically for citizen photos and other public images.
    """
    try:
        # Security check - ensure filename doesn't contain directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Look for the file in the photos directory
        photo_path = file_manager.photos_dir / filename
        
        # Check if file exists
        if not photo_path.exists() or not photo_path.is_file():
            logger.warning(f"Photo not found: {photo_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )
        
        # Determine content type
        content_type = "application/octet-stream"
        file_ext = photo_path.suffix.lower()
        if file_ext in ['.jpg', '.jpeg']:
            content_type = "image/jpeg"
        elif file_ext == '.png':
            content_type = "image/png"
        elif file_ext == '.gif':
            content_type = "image/gif"
        elif file_ext == '.webp':
            content_type = "image/webp"
        
        # Return file with appropriate caching headers
        return FileResponse(
            path=str(photo_path),
            media_type=content_type,
            filename=photo_path.name,
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Access-Control-Allow-Origin": "*"  # Allow cross-origin access
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving photo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve photo: {str(e)}"
        ) 