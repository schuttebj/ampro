import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Configuration - Explicitly list allowed origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://ampro-platform.vercel.app",
        "https://ampro-core-frontend.vercel.app",
        "https://ampro-frontend.vercel.app",
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://localhost:8000",
        "http://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            origins = [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            origins = v
        else:
            origins = []
        
        # Always include known deployment URLs
        required_origins = [
            "https://ampro-platform.vercel.app",
            "https://ampro-core-frontend.vercel.app",
            "https://ampro-frontend.vercel.app"
        ]
        
        for origin in required_origins:
            if origin not in origins:
                origins.append(origin)
                
        return origins

    # Project Information
    PROJECT_NAME: str = "AMPRO License System"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Database
    DATABASE_URL: Optional[PostgresDsn] = os.getenv("DATABASE_URL", None)
    
    # For testing
    TEST_DATABASE_URL: Optional[PostgresDsn] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Verify critical settings
if not settings.DATABASE_URL:
    import logging
    logging.warning("DATABASE_URL is not set in the environment variables. Application may not function correctly.") 