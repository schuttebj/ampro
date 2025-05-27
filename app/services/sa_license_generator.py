"""
Professional South African Driver's License Generator
Based on ISO/IEC 18013-1 standards and SA Department of Transport specifications

Canvas: 85.60 mm × 54 mm, 300 DPI (1012 px × 638 px)
"""

import io
import base64
import json
import os
from typing import Dict, Any, Optional, Tuple
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
import pdf417gen
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# ---------- CONSTANTS ----------
DPI = 300
MM_TO_INCH = 1/25.4
CARD_W_MM = 85.60
CARD_H_MM = 54.00
CARD_W_PX = int(CARD_W_MM * MM_TO_INCH * DPI)   # 1012
CARD_H_PX = int(CARD_H_MM * MM_TO_INCH * DPI)   # 638

# Font sizes (in points) - Updated to achieve ~20px height
FONT_SIZES = {
    "title": 24,
    "subtitle": 16,
    "field_label": 15,    # Increased from 5pt to achieve ~20px height
    "field_value": 15,    # Increased from 5pt to achieve ~20px height
    "small": 10,
    "tiny": 8,
}

# Grid system constants
GUTTER_PX = 23.6
BLEED_PX = 23.6  # 2mm bleed
GRID_COLS = 6
GRID_ROWS = 6

def calculate_grid_positions():
    """Calculate grid cell positions based on 6x6 grid system"""
    # Available space after bleed and gutters
    available_width = CARD_W_PX - (2 * BLEED_PX) - (5 * GUTTER_PX)  # 5 gutters between 6 columns
    available_height = CARD_H_PX - (2 * BLEED_PX) - (5 * GUTTER_PX)  # 5 gutters between 6 rows
    
    cell_width = available_width / GRID_COLS
    cell_height = available_height / GRID_ROWS
    
    grid_positions = {}
    
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = BLEED_PX + (col * (cell_width + GUTTER_PX))
            y = BLEED_PX + (row * (cell_height + GUTTER_PX))
            grid_positions[f"r{row+1}c{col+1}"] = (int(x), int(y), int(cell_width), int(cell_height))
    
    return grid_positions, cell_width, cell_height

# Calculate grid positions
GRID_POSITIONS, CELL_WIDTH, CELL_HEIGHT = calculate_grid_positions()

# Updated coordinates based on grid system
FRONT_COORDINATES = {
    # Photo area: Columns 1-2, Rows 2-5 (2x4 grid cells)
    "photo": (
        GRID_POSITIONS["r2c1"][0],  # x
        GRID_POSITIONS["r2c1"][1],  # y
        GRID_POSITIONS["r2c2"][0] + GRID_POSITIONS["r2c2"][2] - GRID_POSITIONS["r2c1"][0],  # width (2 columns)
        GRID_POSITIONS["r5c1"][1] + GRID_POSITIONS["r5c1"][3] - GRID_POSITIONS["r2c1"][1]   # height (4 rows)
    ),
    
    # Information area: Columns 3-6, Rows 2-5 (starting positions for text)
    "info_start_x": GRID_POSITIONS["r2c3"][0],
    "info_start_y": GRID_POSITIONS["r2c3"][1],
    "info_line_height": 15,  # Spacing between lines
    
    # Signature area: Row 6, Columns 1-6
    "signature": (
        GRID_POSITIONS["r6c1"][0],
        GRID_POSITIONS["r6c1"][1],
        GRID_POSITIONS["r6c6"][0] + GRID_POSITIONS["r6c6"][2] - GRID_POSITIONS["r6c1"][0],
        GRID_POSITIONS["r6c1"][3]
    ),
}

BACK_COORDINATES = {
    # PDF417 barcode area
    "barcode": (30, 340, 30+458, 340+38),
    
    # Fingerprint area
    "fingerprint": (50, 450, 170, 570),
    
    # License categories grid
    "categories_start": (30, 100),
    "category_spacing": (120, 35),
    
    # Restrictions header
    "restrictions_header": (30, 30),
}

# Colors (RGB)
COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "security_pink": (255, 200, 200),
    "security_overlay": (255, 150, 150, 40),
    "watermark": (200, 200, 200, 30),
}

# License categories with descriptions
LICENSE_CATEGORIES = {
    "A": ("Motorcycles", "🏍️"),
    "A1": ("Motorcycles ≤ 125cc", "🛵"),
    "B": ("Light motor vehicles ≤ 3500kg", "🚗"),
    "C1": ("Medium trucks 3500-16000kg", "🚚"),
    "C": ("Heavy trucks > 16000kg", "🚛"),
    "EB": ("Light trailers with B", "🚗🚛"),
    "EC": ("Heavy trailers with C", "🚛🚛"),
}


class SALicenseGenerator:
    """Professional South African Driver's License Generator"""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_path, "..", "assets")
        self.fonts = self._load_fonts()
    
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts with fallbacks for different systems"""
        fonts = {}
        
        # Font search paths
        font_paths = [
            # Custom fonts directory
            os.path.join(self.base_path, "..", "assets", "fonts"),
            # System fonts
            "C:/Windows/Fonts",  # Windows
            "/System/Library/Fonts",  # macOS
            "/usr/share/fonts/truetype/dejavu",  # Linux
        ]
        
        # Font options in order of preference
        font_options = [
            "SourceSansPro-Bold.ttf",
            "SourceSansPro-Regular.ttf", 
            "ARIALBD.TTF",
            "dejavu-sans.bold.ttf",
            "Arial-Bold.ttf",
            "arial.ttf",
            "Arial.ttf",
            "DejaVuSans-Bold.ttf",
            "DejaVuSans.ttf",
        ]
        
        for size_name, size in FONT_SIZES.items():
            font_loaded = False
            
            # Try to find a suitable font
            for font_dir in font_paths:
                if not os.path.exists(font_dir):
                    continue
                    
                for font_file in font_options:
                    font_path = os.path.join(font_dir, font_file)
                    try:
                        fonts[size_name] = ImageFont.truetype(font_path, size)
                        font_loaded = True
                        break
                    except (IOError, OSError):
                        continue
                
                if font_loaded:
                    break
            
            # Fallback to default font
            if not font_loaded:
                fonts[size_name] = ImageFont.load_default()
        
        return fonts
    
    def _create_security_background(self, width: int, height: int) -> Image.Image:
        """Create security background pattern"""
        # Try to load the new grid-based template first
        template_path = os.path.join(self.assets_path, "overlays", "Card_BG_Back.png")
        if os.path.exists(template_path):
            try:
                background = Image.open(template_path).convert('RGBA')
                # Resize to exact dimensions if needed
                if background.size != (width, height):
                    background = background.resize((width, height), Image.Resampling.LANCZOS)
                return background
            except Exception as e:
                print(f"Warning: Could not load Card_BG_Back template: {e}")
        
        # Try to load overlay from file first
        overlay_path = os.path.join(self.assets_path, "overlays", "security_background.png")
        if os.path.exists(overlay_path):
            try:
                background = Image.open(overlay_path).convert('RGBA')
                # Resize to exact dimensions if needed
                if background.size != (width, height):
                    background = background.resize((width, height), Image.Resampling.LANCZOS)
                return background
            except Exception as e:
                print(f"Warning: Could not load security background overlay: {e}")
        
        # Fallback: Create programmatic background
        # Create base with security color
        background = Image.new('RGBA', (width, height), COLORS["white"] + (255,))
        
        # Add security overlay areas (pink/red zones)
        overlay = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Left security area (photo region)
        draw.rectangle([0, 0, width//3, height], fill=COLORS["security_overlay"])
        
        # Right security areas
        draw.rectangle([width*2//3, 0, width, height//2], fill=COLORS["security_overlay"])
        draw.rectangle([width//2, height//2, width, height], fill=(255, 180, 180, 30))
        
        # Combine background and overlay
        background = Image.alpha_composite(background, overlay)
        
        return background
    
    def _create_watermark_pattern(self, width: int, height: int, text: str = "SOUTH AFRICA") -> Image.Image:
        """Create diagonal watermark pattern"""
        # Try to load watermark from file first
        watermark_path = os.path.join(self.assets_path, "overlays", "watermark_pattern.png")
        if os.path.exists(watermark_path):
            try:
                watermark = Image.open(watermark_path).convert('RGBA')
                # Resize to exact dimensions if needed
                if watermark.size != (width, height):
                    watermark = watermark.resize((width, height), Image.Resampling.LANCZOS)
                return watermark
            except Exception as e:
                print(f"Warning: Could not load watermark overlay: {e}")
        
        # Fallback: Create programmatic watermark
        watermark = Image.new('RGBA', (width * 2, height * 2), (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        
        # Use title font for watermark
        font = self.fonts["title"]
        
        # Calculate text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Create diagonal pattern
        for y in range(-text_height, height * 2 + text_height, text_height * 4):
            for x in range(-text_width, width * 2 + text_width, text_width * 3):
                # Alternate between normal and rotated text
                if (x // (text_width * 3) + y // (text_height * 4)) % 2 == 0:
                    draw.text((x, y), text, fill=COLORS["watermark"], font=font)
                else:
                    # Create rotated text
                    temp_img = Image.new('RGBA', (text_width + 40, text_height + 40), (255, 255, 255, 0))
                    temp_draw = ImageDraw.Draw(temp_img)
                    temp_draw.text((20, 20), text, fill=COLORS["watermark"], font=font)
                    rotated = temp_img.rotate(15, expand=1)
                    watermark.paste(rotated, (x, y), rotated)
        
        # Crop to original size
        return watermark.crop((0, 0, width, height))
    
    def _download_and_process_photo(self, photo_url: str) -> Optional[Image.Image]:
        """Download and process photo to exact specifications"""
        if not photo_url:
            return None
        
        try:
            response = requests.get(photo_url, timeout=10)
            response.raise_for_status()
            
            # Open and process the image
            photo = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
            if photo.mode != 'RGB':
                photo = photo.convert('RGB')
            
            # Calculate exact photo dimensions (18 × 22 mm at 300 DPI)
            photo_w = int(18 * MM_TO_INCH * DPI)  # 213 px
            photo_h = int(22 * MM_TO_INCH * DPI)  # 260 px
            
            # Resize maintaining aspect ratio
            photo.thumbnail((photo_w, photo_h), Image.Resampling.LANCZOS)
            
            # Create final photo with exact dimensions
            final_photo = Image.new('RGB', (photo_w, photo_h), COLORS["white"])
            paste_x = (photo_w - photo.width) // 2
            paste_y = (photo_h - photo.height) // 2
            final_photo.paste(photo, (paste_x, paste_y))
            
            return final_photo
            
        except Exception as e:
            print(f"Error processing photo: {e}")
            return None
    
    def _create_government_emblem(self) -> Image.Image:
        """Create South African government emblem"""
        emblem_w = FRONT_COORDINATES["emblem"][2] - FRONT_COORDINATES["emblem"][0]
        emblem_h = FRONT_COORDINATES["emblem"][3] - FRONT_COORDINATES["emblem"][1]
        
        # Try to load emblem from file first
        emblem_path = os.path.join(self.assets_path, "templates", "government_emblem.png")
        if os.path.exists(emblem_path):
            try:
                emblem = Image.open(emblem_path).convert('RGBA')
                # Resize to exact dimensions
                emblem = emblem.resize((emblem_w, emblem_h), Image.Resampling.LANCZOS)
                return emblem
            except Exception as e:
                print(f"Warning: Could not load government emblem: {e}")
        
        # Fallback: Create simplified emblem
        emblem = Image.new('RGBA', (emblem_w, emblem_h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(emblem)
        
        center_x, center_y = emblem_w // 2, emblem_h // 2
        
        # Create simplified coat of arms
        # Shield
        shield_points = [
            (center_x - 25, center_y - 20),
            (center_x + 25, center_y - 20),
            (center_x + 25, center_y + 15),
            (center_x, center_y + 25),
            (center_x - 25, center_y + 15)
        ]
        draw.polygon(shield_points, fill=(0, 100, 0), outline=COLORS["black"], width=2)
        
        # Central elements
        draw.ellipse([center_x - 15, center_y - 10, center_x + 15, center_y + 5], 
                    fill=(255, 255, 0), outline=COLORS["black"], width=1)
        draw.text((center_x, center_y - 2), "RSA", fill=COLORS["black"], 
                 font=self.fonts["small"], anchor="mm")
        
        return emblem
    
    def _generate_pdf417_barcode(self, data: str) -> Image.Image:
        """Generate PDF417 barcode for license data"""
        try:
            # Generate PDF417 barcode
            barcode = pdf417gen.encode(data, columns=14, security_level=5)
            barcode_img = pdf417gen.render_image(barcode, padding=2, scale=2)
            
            # Calculate target size
            target_w = BACK_COORDINATES["barcode"][2] - BACK_COORDINATES["barcode"][0]
            target_h = BACK_COORDINATES["barcode"][3] - BACK_COORDINATES["barcode"][1]
            
            # Resize to fit
            barcode_img = barcode_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            return barcode_img
            
        except Exception as e:
            print(f"Error generating PDF417 barcode: {e}")
            # Return placeholder
            target_w = BACK_COORDINATES["barcode"][2] - BACK_COORDINATES["barcode"][0]
            target_h = BACK_COORDINATES["barcode"][3] - BACK_COORDINATES["barcode"][1]
            placeholder = Image.new('RGB', (target_w, target_h), COLORS["white"])
            draw = ImageDraw.Draw(placeholder)
            draw.rectangle([0, 0, target_w-1, target_h-1], outline=COLORS["black"], width=1)
            draw.text((target_w//2, target_h//2), "BARCODE", fill=COLORS["black"], 
                     font=self.fonts["small"], anchor="mm")
            return placeholder
    
    def generate_front(self, license_data: Dict[str, Any], photo_url: Optional[str] = None) -> str:
        """Generate professional SA license front side using grid-based layout"""
        
        # Create base image with grid-based background template
        license_img = self._create_security_background(CARD_W_PX, CARD_H_PX)
        draw = ImageDraw.Draw(license_img)
        
        # Process and add photo in grid position (Columns 1-2, Rows 2-5)
        photo = self._download_and_process_photo(photo_url)
        photo_pos = FRONT_COORDINATES["photo"]
        
        if photo:
            # Resize photo to fit the grid area
            photo_resized = photo.resize((photo_pos[2], photo_pos[3]), Image.Resampling.LANCZOS)
            license_img.paste(photo_resized, (photo_pos[0], photo_pos[1]))
        else:
            # Photo placeholder (no border)
            draw.rectangle([photo_pos[0], photo_pos[1], 
                          photo_pos[0] + photo_pos[2], photo_pos[1] + photo_pos[3]], 
                         fill=(240, 240, 240))
            photo_center_x = photo_pos[0] + photo_pos[2] // 2
            photo_center_y = photo_pos[1] + photo_pos[3] // 2
            draw.text((photo_center_x, photo_center_y), "PHOTO", 
                     fill=(100, 100, 100), font=self.fonts["field_value"], anchor="mm")
        
        # Information area: Columns 3-6, Rows 2-5 (left-aligned labels and values)
        info_x = FRONT_COORDINATES["info_start_x"]
        info_y = FRONT_COORDINATES["info_start_y"]
        line_height = FRONT_COORDINATES["info_line_height"]
        
        # Define information fields with labels and values
        info_fields = [
            ("Surname", license_data.get('last_name', 'N/A')),
            ("Name", license_data.get('first_name', 'N/A')),
            ("Date of Birth", license_data.get('date_of_birth', 'N/A')),
            ("Gender", license_data.get('gender', 'N/A')),
            ("ID No", license_data.get('id_number', 'N/A')),
            ("Valid", f"{license_data.get('issue_date', 'N/A')} - {license_data.get('expiry_date', 'N/A')}"),
            ("Issued", license_data.get('issued_location', 'South Africa')),
            ("Licence No", license_data.get('license_number', 'N/A')),
            ("Code", license_data.get('category', 'N/A')),
            ("Restrictions", license_data.get('restrictions', '0')),
            ("First Issue", license_data.get('first_issue_date', 'N/A')),
        ]
        
        # Draw information fields with proper spacing
        current_y = info_y
        for label, value in info_fields:
            # Draw label (bold, 5pt)
            draw.text((info_x, current_y), label, 
                     fill=COLORS["black"], font=self.fonts["field_label"])
            
            # Calculate value position (aligned with label)
            label_width = draw.textbbox((0, 0), label, font=self.fonts["field_label"])[2]
            value_x = info_x + label_width + 20  # 20px spacing between label and value
            
            # Draw value (regular, 5pt)
            draw.text((value_x, current_y), str(value), 
                     fill=COLORS["black"], font=self.fonts["field_value"])
            
            current_y += line_height
        
        # Signature area: Row 6, Columns 1-6 (no border)
        sig_box = FRONT_COORDINATES["signature"]
        draw.text((sig_box[0] + 5, sig_box[1] + 5), "Signature:", 
                 fill=COLORS["black"], font=self.fonts["field_label"])
        
        # Convert to base64 (no watermark overlay)
        buffer = io.BytesIO()
        license_img.save(buffer, format="PNG", dpi=(DPI, DPI))
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def generate_back(self, license_data: Dict[str, Any]) -> str:
        """Generate professional SA license back side"""
        
        # Create base image with security background
        license_img = self._create_security_background(CARD_W_PX, CARD_H_PX)
        draw = ImageDraw.Draw(license_img)
        
        # Add border
        draw.rectangle([2, 2, CARD_W_PX-2, CARD_H_PX-2], outline=COLORS["black"], width=2)
        
        # Add restrictions header
        draw.text(BACK_COORDINATES["restrictions_header"], "DRIVER RESTRICTIONS", 
                 fill=COLORS["black"], font=self.fonts["title"])
        draw.text((BACK_COORDINATES["restrictions_header"][0], 
                  BACK_COORDINATES["restrictions_header"][1] + 25), 
                 "Artificial Limb/Mechanical Aids", 
                 fill=COLORS["black"], font=self.fonts["small"])
        
        # Add license categories
        categories_start = BACK_COORDINATES["categories_start"]
        spacing = BACK_COORDINATES["category_spacing"]
        
        draw.text((categories_start[0], categories_start[1] - 20), "LICENCE CATEGORIES", 
                 fill=COLORS["black"], font=self.fonts["field_value"])
        
        for i, (cat, (desc, icon)) in enumerate(LICENSE_CATEGORIES.items()):
            row = i % 4
            col = i // 4
            
            x = categories_start[0] + col * 250
            y = categories_start[1] + row * spacing[1]
            
            # Category box
            draw.rectangle([x, y, x + 30, y + 25], outline=COLORS["black"], width=1)
            draw.text((x + 15, y + 12), cat, fill=COLORS["black"], 
                     font=self.fonts["field_label"], anchor="mm")
            
            # Description
            draw.text((x + 40, y + 12), f"{icon} {desc}", fill=COLORS["black"], 
                     font=self.fonts["small"], anchor="lm")
        
        # Add fingerprint area
        fp_box = BACK_COORDINATES["fingerprint"]
        draw.rectangle(fp_box, outline=COLORS["black"], width=2)
        
        # Create fingerprint pattern
        fp_size = 120
        for i in range(5, fp_size - 5, 3):
            for j in range(5, fp_size - 5, 3):
                if (i + j) % 6 < 3:
                    draw.point((fp_box[0] + i, fp_box[1] + j), fill=COLORS["black"])
        
        draw.text(((fp_box[0] + fp_box[2]) // 2, fp_box[3] + 10), "RIGHT THUMB", 
                 fill=COLORS["black"], font=self.fonts["tiny"], anchor="mm")
        
        # Generate and add PDF417 barcode
        barcode_data = json.dumps({
            "license_number": license_data.get('license_number'),
            "id_number": license_data.get('id_number'),
            "category": license_data.get('category'),
            "expiry_date": str(license_data.get('expiry_date')),
            "issue_date": str(license_data.get('issue_date')),
        })
        
        barcode_img = self._generate_pdf417_barcode(barcode_data)
        barcode_pos = BACK_COORDINATES["barcode"][:2]
        license_img.paste(barcode_img, barcode_pos)
        
        # Add authority information
        draw.text((CARD_W_PX // 2, CARD_H_PX - 20), 
                 "Department of Transport - Republic of South Africa", 
                 fill=COLORS["black"], font=self.fonts["tiny"], anchor="mm")
        
        # Convert to base64 (no watermark overlay)
        buffer = io.BytesIO()
        license_img.save(buffer, format="PNG", dpi=(DPI, DPI))
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def generate_watermark_template(self, width: int = CARD_W_PX, height: int = CARD_H_PX, 
                                  text: str = "SOUTH AFRICA") -> str:
        """Generate standalone watermark template"""
        watermark = self._create_watermark_pattern(width, height, text)
        
        buffer = io.BytesIO()
        watermark.save(buffer, format="PNG", dpi=(DPI, DPI))
        return base64.b64encode(buffer.getvalue()).decode('utf-8')


# Singleton instance
sa_license_generator = SALicenseGenerator()


# Public API functions
def generate_sa_license_front_professional(license_data: Dict[str, Any], 
                                         photo_url: Optional[str] = None) -> str:
    """Generate professional SA license front side"""
    return sa_license_generator.generate_front(license_data, photo_url)


def generate_sa_license_back_professional(license_data: Dict[str, Any]) -> str:
    """Generate professional SA license back side"""
    return sa_license_generator.generate_back(license_data)


def generate_watermark_template_professional(width: int = CARD_W_PX, height: int = CARD_H_PX, 
                                           text: str = "SOUTH AFRICA") -> str:
    """Generate professional watermark template"""
    return sa_license_generator.generate_watermark_template(width, height, text)


def get_license_specifications() -> Dict[str, Any]:
    """Get license specifications and coordinates"""
    return {
        "dimensions": {
            "width_mm": CARD_W_MM,
            "height_mm": CARD_H_MM,
            "width_px": CARD_W_PX,
            "height_px": CARD_H_PX,
            "dpi": DPI,
        },
        "coordinates": {
            "front": FRONT_COORDINATES,
            "back": BACK_COORDINATES,
        },
        "font_sizes": FONT_SIZES,
        "colors": COLORS,
        "license_categories": LICENSE_CATEGORIES,
    } 