# AMPRO Production License System

## Overview

The AMPRO Production License System is an enterprise-ready implementation for generating South African driver's licenses with complete file management, ISO compliance, and production-grade features.

## Key Features

### 1. File Storage & Management
- **Persistent Storage**: All generated files are stored on disk with database references
- **Smart Cleanup**: Automatic removal of old files when new ones are generated
- **Version Control**: Track generation versions and force regeneration when needed
- **Multiple Formats**: Generate PNG images and PDF documents

### 2. ISO-Compliant Photo Processing
- **Automatic Cropping**: Images are cropped to exact ISO specifications (18×22mm at 300 DPI)
- **Quality Enhancement**: Subtle sharpening and contrast adjustment for license quality
- **Format Standardization**: All photos saved as high-quality JPEG at 300 DPI
- **Size Validation**: Ensures photos meet exact pixel requirements (213×260 pixels)

### 3. Production-Ready License Generation
- **Professional Templates**: Uses enhanced SA license generator with proper assets
- **PDF417 Barcodes**: ISO/IEC 15438 compliant barcodes with security level 5
- **Multiple Output Formats**: PNG images and PDF documents
- **Combined Documents**: Single PDF with both front and back sides

### 4. Advanced Storage Management
- **Organized Structure**: Separate directories for licenses, photos, and temporary files
- **Hash-Based Naming**: Prevents duplicate storage using content hashes
- **Background Cleanup**: Automatic cleanup of temporary files
- **Storage Statistics**: Monitor disk usage and file counts

## API Endpoints

### Core License Generation

#### Generate Complete License Package
```http
POST /api/v1/licenses/{license_id}/generate
```
Generates all license files (front, back, PDFs) and stores them with database references.

**Parameters:**
- `force_regenerate` (boolean): Force regeneration even if files exist

**Response:**
```json
{
  "message": "License files generated successfully",
  "license_id": 123,
  "license_number": "L-ABCD-1234-EFGH",
  "files": {
    "front_image_path": "licenses/license_123_front.png",
    "back_image_path": "licenses/license_123_back.png",
    "front_pdf_path": "licenses/license_123_front.pdf",
    "back_pdf_path": "licenses/license_123_back.pdf",
    "combined_pdf_path": "licenses/license_123_combined.pdf",
    "front_image_url": "/static/storage/licenses/license_123_front.png",
    "back_image_url": "/static/storage/licenses/license_123_back.png",
    "generation_timestamp": "2024-01-15T10:30:00",
    "generator_version": "2.0"
  },
  "cached": false
}
```

#### Get License File Information
```http
GET /api/v1/licenses/{license_id}/files
```
Returns information about generated license files.

#### Download License Files
```http
GET /api/v1/licenses/{license_id}/download/{file_type}
```
Download specific license files.

**File Types:**
- `front_image` - Front side PNG
- `back_image` - Back side PNG
- `front_pdf` - Front side PDF
- `back_pdf` - Back side PDF
- `combined_pdf` - Combined front/back PDF

### Photo Management

#### Update License Photo
```http
POST /api/v1/licenses/{license_id}/photo/update
```
Updates citizen photo and triggers license regeneration.

**Body:**
```json
{
  "photo_url": "https://example.com/photo.jpg"
}
```

### Storage Management

#### Get Storage Statistics
```http
GET /api/v1/licenses/storage/stats
```
Returns storage system statistics.

#### Trigger Storage Cleanup
```http
POST /api/v1/licenses/storage/cleanup
```
Initiates background cleanup of temporary files.

## File Structure

```
app/static/storage/
├── licenses/           # Generated license files
│   ├── license_1_front.png
│   ├── license_1_back.png
│   ├── license_1_combined.pdf
│   └── ...
├── photos/            # Citizen photos
│   ├── citizen_1_original_abc123.jpg
│   ├── citizen_1_processed_abc123.jpg
│   └── ...
└── temp/              # Temporary files (auto-cleaned)
    └── ...
```

## Database Schema

### License Table Additions
```sql
-- File storage paths
front_image_path VARCHAR NULL
back_image_path VARCHAR NULL
front_pdf_path VARCHAR NULL
back_pdf_path VARCHAR NULL
combined_pdf_path VARCHAR NULL

-- Photo processing tracking
original_photo_path VARCHAR NULL
processed_photo_path VARCHAR NULL
photo_last_updated DATETIME NULL

-- Generation metadata
last_generated DATETIME NULL
generation_version VARCHAR NOT NULL DEFAULT '1.0'
```

### Citizen Table Additions
```sql
-- Photo management
stored_photo_path VARCHAR NULL
processed_photo_path VARCHAR NULL
photo_uploaded_at DATETIME NULL
photo_processed_at DATETIME NULL
```

## ISO Specifications

### Photo Requirements
- **Physical Size**: 18×22mm
- **Digital Size**: 213×260 pixels at 300 DPI
- **Format**: JPEG with 95% quality
- **Processing**: Automatic cropping, sharpening, and contrast enhancement

### License Card Specifications
- **Physical Size**: 85.60×54.00mm (ISO/IEC 7810 ID-1)
- **Digital Size**: 1012×638 pixels at 300 DPI
- **Barcode**: PDF417 with security level 5
- **Colors**: Security pink overlays and watermarks

## Maintenance & Management

### Command Line Tools

Process citizen photos:
```bash
python app/scripts/maintenance.py process-photos --batch-size 50
```

Regenerate licenses:
```bash
python app/scripts/maintenance.py regenerate-licenses --version-cutoff 2.0 --batch-size 20
```

Clean up storage:
```bash
python app/scripts/maintenance.py cleanup-storage --older-than-hours 24
```

Get storage statistics:
```bash
python app/scripts/maintenance.py storage-stats
```

### Background Tasks

The system uses FastAPI's BackgroundTasks for:
- Automatic cleanup of temporary files
- Batch processing operations
- Non-blocking file operations

### Error Handling

- **Photo Processing Errors**: Logged and skip to next citizen
- **Generation Errors**: Return HTTP 500 with detailed error message
- **File System Errors**: Graceful degradation with fallbacks
- **Storage Full**: Monitor disk space and alert when threshold reached

## Security Features

### File Security
- Files stored outside web root by default
- Access controlled through authenticated endpoints
- Content-based hashing prevents tampering
- Regular cleanup of sensitive temporary files

### Audit Trail
- All file generation and downloads logged
- User action tracking for compliance
- Storage access monitoring

## Performance Optimization

### Caching Strategy
- Files generated once and cached until regeneration needed
- Database tracking of generation timestamps
- Smart cache invalidation based on version changes

### Batch Processing
- Support for bulk photo processing
- Batch license regeneration
- Background processing for non-urgent tasks

### Resource Management
- Configurable batch sizes
- Memory-efficient image processing
- Automatic cleanup of temporary resources

## Configuration

### Environment Variables
```bash
# Storage configuration
AMPRO_STORAGE_DIR=/path/to/storage  # Default: app/static/storage

# Processing configuration
PHOTO_PROCESSING_QUALITY=95
LICENSE_GENERATION_DPI=300
CLEANUP_INTERVAL_HOURS=24
```

### Database Migration
```bash
# Apply the new schema
alembic upgrade head
```

## Deployment Considerations

### Storage Requirements
- Plan for ~2-5MB per license (all files combined)
- ~500KB per processed citizen photo
- Regular cleanup reduces temporary file accumulation

### Backup Strategy
- Include storage directory in backup procedures
- Database contains file path references
- Consider cloud storage integration for large deployments

### Monitoring
- Monitor disk space usage
- Track file generation success rates
- Alert on processing failures

## Future Enhancements

### Planned Features
- Cloud storage integration (AWS S3, Azure Blob)
- Advanced photo validation (face detection, quality checks)
- Batch printing integration
- Real-time processing status tracking

### API Versioning
- Current version: 2.0
- Backward compatibility maintained
- Version-based regeneration triggers

## Support & Troubleshooting

### Common Issues
1. **Photo Processing Fails**: Check URL accessibility and image format
2. **Storage Full**: Run cleanup or increase disk space
3. **Generation Errors**: Check asset files and font availability
4. **Database Inconsistency**: Run maintenance scripts to sync file references

### Logging
- File operations logged at INFO level
- Errors logged with full stack traces
- Storage statistics available via API

For technical support, check the logs in `app/logs/` and run the maintenance scripts with `--dry-run` flag for diagnostics. 