from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import logging

from app.core.config import settings
from app.api.routes import api_router
from app.core.security import get_current_active_user
from app.services.file_manager import file_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for driver's license processing system",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize things on app startup"""
    logger.info("Creating storage directories...")
    try:
        # Ensure all storage directories exist
        file_manager._ensure_directories()
        
        # Check that photos directory exists and is writable
        photos_dir = file_manager.photos_dir
        if os.path.exists(photos_dir):
            logger.info(f"Photos directory exists at {photos_dir}")
            if os.access(photos_dir, os.W_OK):
                logger.info("Photos directory is writable")
            else:
                logger.warning("Photos directory is not writable!")
        else:
            logger.warning(f"Photos directory does not exist at {photos_dir}")
            
        # Check storage stats
        stats = file_manager.get_storage_stats()
        logger.info(f"Storage directories created. Total files: {stats['total_files']}")
        
    except Exception as e:
        logger.error(f"Error initializing storage: {str(e)}")

@app.get("/")
async def root():
    """
    Root endpoint for health check.
    """
    return {
        "message": "Welcome to AMPRO License System API",
        "status": "healthy",
        "version": "0.1.0",
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "api_version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }

@app.get("/protected")
async def protected_route(current_user = Depends(get_current_active_user)):
    """
    Protected route example to test authentication.
    """
    return {
        "message": "This is a protected route",
        "user_id": current_user.id,
        "username": current_user.username,
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 