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

# Exact coordinates based on SA license template (in pixels at 300 DPI)
FRONT_COORDINATES = {
    # Photo area: 18 × 22 mm = 213 × 260 px
    "photo": (40, 58, 40+213, 58+260),  # (x0, y0, x1, y1)
    
    # Text field positions (x, y)
    "surname": (530, 80),
    "names": (530, 125),
    "id_number": (530, 170),
    "date_of_birth": (530, 215),
    "issue_date": (530, 260),
    "expiry_date": (530, 305),
    "license_number": (530, 350),
    "category": (530, 395),
    "restrictions": (530, 440),
    
    # Signature box
    "signature": (530, 485, 885, 540),
    
    # Government emblem
    "emblem": (20, 20, 120, 80),
    
    # Title position
    "title": (CARD_W_PX // 2, 30),
    "subtitle": (CARD_W_PX // 2, 55),
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

# Font sizes (in points)
FONT_SIZES = {
    "title": 24,
    "subtitle": 16,
    "field_label": 12,
    "field_value": 14,
    "small": 10,
    "tiny": 8,
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
        """Generate professional SA license front side"""
        
        # Create base image with security background
        license_img = self._create_security_background(CARD_W_PX, CARD_H_PX)
        draw = ImageDraw.Draw(license_img)
        
        # Add border
        draw.rectangle([2, 2, CARD_W_PX-2, CARD_H_PX-2], outline=COLORS["black"], width=2)
        
        # Add government emblem
        emblem = self._create_government_emblem()
        emblem_pos = FRONT_COORDINATES["emblem"][:2]
        license_img.paste(emblem, emblem_pos, emblem)
        
        # Add title and subtitle
        draw.text(FRONT_COORDINATES["title"], "DRIVING LICENCE", 
                 fill=COLORS["black"], font=self.fonts["title"], anchor="mm")
        draw.text(FRONT_COORDINATES["subtitle"], "REPUBLIC OF SOUTH AFRICA", 
                 fill=COLORS["black"], font=self.fonts["subtitle"], anchor="mm")
        
        # Process and add photo
        photo = self._download_and_process_photo(photo_url)
        photo_pos = FRONT_COORDINATES["photo"]
        
        if photo:
            license_img.paste(photo, photo_pos[:2])
        else:
            # Photo placeholder
            draw.rectangle(photo_pos, outline=COLORS["black"], width=2, fill=(240, 240, 240))
            photo_center_x = (photo_pos[0] + photo_pos[2]) // 2
            photo_center_y = (photo_pos[1] + photo_pos[3]) // 2
            draw.text((photo_center_x, photo_center_y), "PHOTO", 
                     fill=(100, 100, 100), font=self.fonts["field_value"], anchor="mm")
        
        # Add photo border
        draw.rectangle(photo_pos, outline=COLORS["black"], width=2)
        
        # Add text fields
        fields = [
            ("surname", f"Surname: {license_data.get('last_name', 'N/A')}"),
            ("names", f"Names: {license_data.get('first_name', 'N/A')}"),
            ("id_number", f"ID No: {license_data.get('id_number', 'N/A')}"),
            ("date_of_birth", f"Date of Birth: {license_data.get('date_of_birth', 'N/A')}"),
            ("issue_date", f"Issue: {license_data.get('issue_date', 'N/A')}"),
            ("expiry_date", f"Valid: {license_data.get('expiry_date', 'N/A')}"),
            ("license_number", f"DL No: {license_data.get('license_number', 'N/A')}"),
            ("category", f"Code: {license_data.get('category', 'N/A')}"),
        ]
        
        for field_name, text in fields:
            pos = FRONT_COORDINATES[field_name]
            draw.text(pos, text, fill=COLORS["black"], font=self.fonts["field_value"])
        
        # Add restrictions if any
        if license_data.get('restrictions'):
            restrictions_text = f"Restrictions: {license_data.get('restrictions')}"
            draw.text(FRONT_COORDINATES["restrictions"], restrictions_text, 
                     fill=COLORS["black"], font=self.fonts["small"])
        
        # Add signature box
        sig_box = FRONT_COORDINATES["signature"]
        draw.rectangle(sig_box, outline=COLORS["black"], width=1)
        draw.text((sig_box[0] + 5, sig_box[1] + 5), "Signature:", 
                 fill=COLORS["black"], font=self.fonts["small"])
        
        # Add watermark
        watermark = self._create_watermark_pattern(CARD_W_PX, CARD_H_PX)
        license_img = Image.alpha_composite(license_img.convert('RGBA'), watermark).convert('RGB')
        
        # Add holographic security strip (right edge)
        draw = ImageDraw.Draw(license_img)  # Recreate draw after alpha composite
        security_strip_x = CARD_W_PX - 25
        for i in range(0, CARD_H_PX, 8):
            color = (200 + (i % 55), 150 + (i % 105), 255)
            draw.rectangle([security_strip_x, i, CARD_W_PX - 2, i + 4], fill=color)
        
        # Convert to base64
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
        
        # Add watermark
        watermark = self._create_watermark_pattern(CARD_W_PX, CARD_H_PX)
        license_img = Image.alpha_composite(license_img.convert('RGBA'), watermark).convert('RGB')
        
        # Add authority information
        draw = ImageDraw.Draw(license_img)  # Recreate draw after alpha composite
        draw.text((CARD_W_PX // 2, CARD_H_PX - 20), 
                 "Department of Transport - Republic of South Africa", 
                 fill=COLORS["black"], font=self.fonts["tiny"], anchor="mm")
        
        # Convert to base64
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