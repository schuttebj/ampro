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

# Log CORS settings
logger.info(f"Configuring CORS with frontend origins for authentication")

# CORS configuration for production with credentials support
frontend_origins = [
    "https://ampro-platform.vercel.app",  # Production frontend
    "http://localhost:3000",              # Development frontend
    "http://localhost:3001",              # Alternative dev port
]

# Add configured backend CORS origins if they exist
if settings.BACKEND_CORS_ORIGINS:
    frontend_origins.extend(settings.BACKEND_CORS_ORIGINS)

logger.info(f"Allowing CORS origins: {frontend_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,  # Specific origins for credential support
    allow_credentials=True,          # Enable credentials for authentication
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=600,  # Cache preflight requests for 10 minutes
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

# Add a HEAD method handler for the root endpoint
@app.head("/")
async def head_root():
    """
    HEAD method for root endpoint.
    """
    return {}

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

# Add a HEAD method handler for the health endpoint
@app.head("/health")
async def head_health():
    """
    HEAD method for health endpoint.
    """
    return {}

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

# Add an OPTIONS handler for the auth/login endpoint to respond to preflight requests
@app.options("/api/v1/auth/login")
async def auth_login_options():
    """
    Handle OPTIONS requests for auth/login endpoint.
    """
    return {"detail": "OK"}

# Add a HEAD handler for the auth/login endpoint
@app.head("/api/v1/auth/login")
async def auth_login_head():
    """
    Handle HEAD requests for auth/login endpoint.
    """
    return {}

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