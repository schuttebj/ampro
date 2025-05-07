#!/usr/bin/env python
"""
Script to run the application locally with the development server.
This will also create initial users if they don't exist.
"""

import uvicorn
import logging
import argparse
from init_db import init_db
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to run the application with development server.
    """
    parser = argparse.ArgumentParser(description="Run the AMPRO License System locally")
    parser.add_argument("--host", default="127.0.0.1", help="Host to listen on")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--skip-init-db", action="store_true", help="Skip database initialization")
    args = parser.parse_args()

    # Initialize database with initial users if needed
    if not args.skip_init_db:
        logger.info("Initializing database with default users")
        db = SessionLocal()
        init_db(db)
        db.close()
    
    # Run the application
    logger.info(f"Starting server at http://{args.host}:{args.port}")
    logger.info(f"API documentation available at http://{args.host}:{args.port}/docs")
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main() 