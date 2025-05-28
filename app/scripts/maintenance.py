#!/usr/bin/env python3
"""
AMPRO License System Maintenance Script

This script provides maintenance functions for:
- Batch photo processing
- Storage cleanup
- License regeneration
- Database maintenance
"""

import argparse
import logging
from typing import List
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app import crud
from app.services.file_manager import file_manager
from app.services.production_license_generator import production_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def process_citizen_photos(batch_size: int = 50, dry_run: bool = False):
    """
    Process photos for citizens who don't have processed photos yet
    
    Args:
        batch_size: Number of citizens to process at once
        dry_run: If True, only show what would be processed
    """
    logger.info(f"Starting photo processing (batch_size={batch_size}, dry_run={dry_run})")
    
    db = next(get_db())
    
    try:
        # Get citizens without processed photos
        citizens = crud.citizen.get_citizens_without_processed_photos(
            db, skip=0, limit=batch_size
        )
        
        if not citizens:
            logger.info("No citizens found that need photo processing")
            return
        
        logger.info(f"Found {len(citizens)} citizens needing photo processing")
        
        for citizen in citizens:
            if dry_run:
                logger.info(f"Would process photo for citizen {citizen.id_number}: {citizen.first_name} {citizen.last_name}")
                continue
            
            try:
                if not citizen.photo_url:
                    logger.warning(f"Citizen {citizen.id_number} has no photo URL, skipping")
                    continue
                
                logger.info(f"Processing photo for citizen {citizen.id_number}")
                
                # Download and process photo
                original_path, processed_path = file_manager.download_and_store_photo(
                    citizen.photo_url, citizen.id
                )
                
                # Update database
                crud.citizen.update_photo_paths(
                    db,
                    citizen_id=citizen.id,
                    stored_photo_path=original_path,
                    processed_photo_path=processed_path
                )
                
                logger.info(f"Successfully processed photo for citizen {citizen.id_number}")
                
            except Exception as e:
                logger.error(f"Error processing photo for citizen {citizen.id_number}: {str(e)}")
        
        db.commit()
        logger.info("Photo processing completed")
        
    except Exception as e:
        logger.error(f"Error during photo processing: {str(e)}")
        db.rollback()
    finally:
        db.close()


def regenerate_licenses(version_cutoff: str = "1.0", batch_size: int = 20, dry_run: bool = False):
    """
    Regenerate licenses that need updating
    
    Args:
        version_cutoff: Minimum version required
        batch_size: Number of licenses to process at once
        dry_run: If True, only show what would be regenerated
    """
    logger.info(f"Starting license regeneration (version_cutoff={version_cutoff}, batch_size={batch_size}, dry_run={dry_run})")
    
    db = next(get_db())
    
    try:
        # Get licenses needing regeneration
        licenses = crud.license.get_licenses_needing_regeneration(
            db, version_cutoff=version_cutoff, skip=0, limit=batch_size
        )
        
        if not licenses:
            logger.info("No licenses found that need regeneration")
            return
        
        logger.info(f"Found {len(licenses)} licenses needing regeneration")
        
        for license in licenses:
            if dry_run:
                logger.info(f"Would regenerate license {license.license_number} (version: {license.generation_version})")
                continue
            
            try:
                logger.info(f"Regenerating license {license.license_number}")
                
                # Get citizen data
                citizen = crud.citizen.get(db, id=license.citizen_id)
                if not citizen:
                    logger.error(f"Citizen not found for license {license.license_number}")
                    continue
                
                # Prepare data
                license_data = {
                    "id": license.id,
                    "license_number": license.license_number,
                    "category": license.category.value,
                    "issue_date": license.issue_date,
                    "expiry_date": license.expiry_date,
                    "status": license.status.value,
                    "restrictions": license.restrictions,
                    "medical_conditions": license.medical_conditions,
                    "barcode_data": license.barcode_data,
                }
                
                citizen_data = {
                    "id": citizen.id,
                    "id_number": citizen.id_number,
                    "first_name": citizen.first_name,
                    "last_name": citizen.last_name,
                    "middle_name": citizen.middle_name,
                    "date_of_birth": citizen.date_of_birth,
                    "gender": citizen.gender.value,
                    "address_line1": citizen.address_line1,
                    "address_line2": citizen.address_line2,
                    "city": citizen.city,
                    "postal_code": citizen.postal_code,
                    "photo_url": citizen.photo_url,
                    "processed_photo_path": citizen.processed_photo_path,
                }
                
                # Generate license
                result = production_generator.generate_complete_license(
                    license_data, citizen_data, force_regenerate=True
                )
                
                # Update database
                crud.license.update_file_paths(db, license_id=license.id, file_paths=result)
                
                logger.info(f"Successfully regenerated license {license.license_number}")
                
            except Exception as e:
                logger.error(f"Error regenerating license {license.license_number}: {str(e)}")
        
        db.commit()
        logger.info("License regeneration completed")
        
    except Exception as e:
        logger.error(f"Error during license regeneration: {str(e)}")
        db.rollback()
    finally:
        db.close()


def cleanup_storage(older_than_hours: int = 24, cleanup_temp: bool = True, 
                   cleanup_orphaned: bool = False, dry_run: bool = False):
    """
    Clean up storage system
    
    Args:
        older_than_hours: Remove temp files older than this many hours
        cleanup_temp: Whether to clean temporary files
        cleanup_orphaned: Whether to clean orphaned files (not in database)
        dry_run: If True, only show what would be cleaned
    """
    logger.info(f"Starting storage cleanup (older_than_hours={older_than_hours}, dry_run={dry_run})")
    
    if cleanup_temp:
        logger.info("Cleaning temporary files...")
        if not dry_run:
            file_manager.cleanup_temp_files(older_than_hours)
        else:
            logger.info(f"Would clean temp files older than {older_than_hours} hours")
    
    if cleanup_orphaned:
        logger.info("Cleaning orphaned files...")
        # This would require checking database references
        # Implementation depends on specific requirements
        if dry_run:
            logger.info("Would clean orphaned files (not implemented yet)")
    
    # Get storage stats
    stats = file_manager.get_storage_stats()
    logger.info(f"Storage stats: {stats}")


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description="AMPRO License System Maintenance")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    subparsers = parser.add_subparsers(dest="command", help="Maintenance commands")
    
    # Photo processing command
    photo_parser = subparsers.add_parser("process-photos", help="Process citizen photos")
    photo_parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    
    # License regeneration command
    regen_parser = subparsers.add_parser("regenerate-licenses", help="Regenerate licenses")
    regen_parser.add_argument("--version-cutoff", default="1.0", help="Minimum version required")
    regen_parser.add_argument("--batch-size", type=int, default=20, help="Batch size for processing")
    
    # Storage cleanup command
    cleanup_parser = subparsers.add_parser("cleanup-storage", help="Clean up storage")
    cleanup_parser.add_argument("--older-than-hours", type=int, default=24, help="Remove temp files older than this many hours")
    cleanup_parser.add_argument("--cleanup-temp", action="store_true", default=True, help="Clean temporary files")
    cleanup_parser.add_argument("--cleanup-orphaned", action="store_true", help="Clean orphaned files")
    
    # Storage stats command
    stats_parser = subparsers.add_parser("storage-stats", help="Show storage statistics")
    
    args = parser.parse_args()
    
    if args.command == "process-photos":
        process_citizen_photos(
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
    elif args.command == "regenerate-licenses":
        regenerate_licenses(
            version_cutoff=args.version_cutoff,
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
    elif args.command == "cleanup-storage":
        cleanup_storage(
            older_than_hours=args.older_than_hours,
            cleanup_temp=args.cleanup_temp,
            cleanup_orphaned=args.cleanup_orphaned,
            dry_run=args.dry_run
        )
    elif args.command == "storage-stats":
        stats = file_manager.get_storage_stats()
        print("\nStorage Statistics:")
        print(f"Total files: {stats['total_files']}")
        print(f"Total size: {stats['total_size_bytes']:,} bytes")
        print(f"License files: {stats['license_files']}")
        print(f"Photo files: {stats['photo_files']}")
        print(f"Temp files: {stats['temp_files']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 