from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
import shutil
import logging

from app import crud
from app.api.v1.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.file_manager import file_manager
from app.models.audit import ActionType, ResourceType

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
    Serve a file from storage.
    """
    try:
        # Get full file path
        full_path = file_manager.base_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Determine media type
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            media_type = f"image/{file_path.split('.')[-1].lower()}"
        elif file_path.lower().endswith('.pdf'):
            media_type = "application/pdf"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=str(full_path),
            media_type=media_type,
            filename=full_path.name
        )
        
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error serving file: {str(e)}"
        ) 