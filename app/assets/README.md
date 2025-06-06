# AMPRO License Assets

This directory contains assets for professional South African driver's license generation.

## Directory Structure

```
assets/
├── templates/          # Base template files (PNG)
│   ├── government_emblem.png      # SA coat of arms (100x60px)
│   ├── sa_front_base.png          # Front template (1012x638px)
│   └── sa_back_base.png           # Back template (1012x638px)
├── fonts/             # Font files (.ttf, .otf)
│   ├── SourceSansPro-Bold.ttf     # Primary bold font
│   ├── SourceSansPro-Regular.ttf  # Primary regular font
│   └── Arial-Bold.ttf             # Fallback font
├── overlays/          # Security overlays and watermarks
│   ├── security_background.png    # Pink/red security pattern (1012x638px)
│   ├── watermark_pattern.png      # "SOUTH AFRICA" diagonal pattern
│   └── holographic_strip.png      # Rainbow security strip
├── sa_license_coordinates.csv     # Exact coordinate mappings
└── README.md          # This file
```

## Asset Loading Behavior

The generator uses a **smart fallback system**:

1. **First**: Try to load professional assets from files
2. **Fallback**: Generate programmatic alternatives if files are missing
3. **Graceful**: Never fails - always produces a license

### Security Background
- **File**: `overlays/security_background.png` (1012×638px, RGBA)
- **Fallback**: Programmatic pink/red security areas
- **Usage**: Loaded automatically for authentic appearance

### Watermark Pattern  
- **File**: `overlays/watermark_pattern.png` (1012×638px, RGBA)
- **Fallback**: Generated "SOUTH AFRICA" diagonal text
- **Usage**: Semi-transparent overlay for security

### Government Emblem
- **File**: `templates/government_emblem.png` (100×60px, RGBA)
- **Fallback**: Simplified shield with "RSA" text
- **Usage**: Official SA coat of arms on front side

### Fonts
- **Files**: Various .ttf files in `fonts/` directory
- **Fallback**: System fonts (Arial, DejaVu) then default
- **Usage**: Professional typography matching real licenses

## Specifications

- **Canvas Size**: 85.60 mm × 54.00 mm (ISO/IEC 18013-1 standard)
- **Resolution**: 300 DPI
- **Pixel Dimensions**: 1012 × 638 pixels
- **Format**: PNG with transparency support
- **Color Space**: CMYK for print, RGB for digital

## Coordinate System

All coordinates are specified in pixels at 300 DPI:
- Origin (0,0) is top-left corner
- X increases rightward
- Y increases downward

See `sa_license_coordinates.csv` for exact positioning.

## Photo Specifications

- **Size**: 18 × 22 mm (213 × 260 pixels at 300 DPI)
- **Position**: (40, 58) top-left corner
- **Format**: RGB, JPEG or PNG
- **Quality**: High resolution for biometric compliance

## Barcode Specifications

- **Type**: PDF417 (ISO/IEC 15438)
- **Position**: Back side, (30, 340)
- **Size**: 458 × 38 pixels
- **Data**: JSON with license details
- **Error Correction**: Level 5

## Font Requirements

Recommended fonts (in order of preference):
1. SourceSansPro-Bold.ttf
2. SourceSansPro-Regular.ttf
3. Arial-Bold.ttf
4. arial.ttf

Font sizes:
- Title: 24pt
- Subtitle: 16pt
- Field values: 14pt
- Field labels: 12pt
- Small text: 10pt
- Tiny text: 8pt

## Security Features

1. **Watermark**: "SOUTH AFRICA" diagonal pattern
2. **Security Background**: Pink/red overlay areas
3. **Holographic Strip**: Right edge rainbow pattern
4. **Microtext**: Small authority information
5. **PDF417 Barcode**: Tamper-evident data encoding

## Usage

```python
from app.services.sa_license_generator import (
    generate_sa_license_front_professional,
    generate_sa_license_back_professional
)

# Generate front side
front_image = generate_sa_license_front_professional(
    license_data, 
    photo_url="https://example.com/photo.jpg"
)

# Generate back side
back_image = generate_sa_license_back_professional(license_data)
```

## API Endpoints

- `GET /api/v1/licenses/{id}/preview/front/professional`
- `GET /api/v1/licenses/{id}/preview/back/professional`
- `GET /api/v1/licenses/watermark-template/professional`
- `GET /api/v1/licenses/specifications`

## Compliance

This implementation follows:
- ISO/IEC 18013-1 (Machine readable travel documents)
- South African Department of Transport specifications
- ICAO Document 9303 (Machine readable travel documents)

## File Naming Convention

- `front_base.png` - Front template without dynamic data
- `back_base.png` - Back template without dynamic data
- `watermark_pattern.png` - Standalone watermark
- `security_overlay.png` - Security background pattern

## Development Notes

1. All measurements are exact to prevent scaling issues
2. Photo processing maintains aspect ratio
3. Barcode generation includes error handling
4. Font loading has multiple fallbacks
5. Color values are consistent across templates 