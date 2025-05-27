import io
import base64
import json
import requests
from typing import Dict, Any, Optional
from datetime import date, datetime
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap


def serialize_date(obj):
    """Helper function to serialize dates to ISO format strings"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def load_fonts():
    """Load fonts with fallbacks for different systems"""
    fonts = {}
    
    # Try to load different fonts with fallbacks
    font_options = [
        "arial.ttf", "Arial.ttf", "DejaVuSans.ttf", 
        "/System/Library/Fonts/Arial.ttf",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "C:/Windows/Fonts/arial.ttf"  # Windows
    ]
    
    for size_name, size in [("title", 24), ("large", 18), ("regular", 14), ("small", 12), ("tiny", 10)]:
        for font_path in font_options:
            try:
                fonts[size_name] = ImageFont.truetype(font_path, size)
                break
            except (IOError, OSError):
                continue
        else:
            # Fallback to default font
            fonts[size_name] = ImageFont.load_default()
    
    return fonts


def create_watermark_pattern(width, height, text="SOUTH AFRICA", opacity=30):
    """Create a repeating watermark pattern"""
    # Create a larger canvas for the pattern
    pattern_width = width * 2
    pattern_height = height * 2
    watermark = Image.new('RGBA', (pattern_width, pattern_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark)
    
    # Load font for watermark
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except (IOError, OSError):
        font = ImageFont.load_default()
    
    # Calculate text dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Create diagonal pattern
    for y in range(-text_height, pattern_height + text_height, text_height * 3):
        for x in range(-text_width, pattern_width + text_width, text_width * 2):
            # Alternate between normal and rotated text
            if (x // (text_width * 2) + y // (text_height * 3)) % 2 == 0:
                draw.text((x, y), text, fill=(200, 200, 200, opacity), font=font)
            else:
                # Create rotated text
                temp_img = Image.new('RGBA', (text_width + 20, text_height + 20), (255, 255, 255, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                temp_draw.text((10, 10), text, fill=(200, 200, 200, opacity), font=font)
                rotated = temp_img.rotate(15, expand=1)
                watermark.paste(rotated, (x, y), rotated)
    
    # Crop to original size
    watermark = watermark.crop((0, 0, width, height))
    return watermark


def download_and_process_photo(photo_url: str, target_size=(140, 180)) -> Optional[Image.Image]:
    """Download and process photo from URL"""
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
        
        # Resize to target size maintaining aspect ratio
        photo.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Create a new image with exact target size and paste the photo centered
        final_photo = Image.new('RGB', target_size, (255, 255, 255))
        paste_x = (target_size[0] - photo.width) // 2
        paste_y = (target_size[1] - photo.height) // 2
        final_photo.paste(photo, (paste_x, paste_y))
        
        return final_photo
        
    except Exception as e:
        print(f"Error processing photo: {e}")
        return None


def create_sa_coat_of_arms(size=(60, 60)):
    """Create a simplified South African coat of arms placeholder"""
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Create a simplified coat of arms representation
    center_x, center_y = size[0] // 2, size[1] // 2
    
    # Shield outline
    shield_points = [
        (center_x - 20, center_y - 25),
        (center_x + 20, center_y - 25),
        (center_x + 20, center_y + 10),
        (center_x, center_y + 25),
        (center_x - 20, center_y + 10)
    ]
    draw.polygon(shield_points, fill=(0, 100, 0), outline=(0, 0, 0), width=2)
    
    # Add some details
    draw.ellipse([center_x - 10, center_y - 15, center_x + 10, center_y - 5], fill=(255, 255, 0))
    draw.text((center_x, center_y), "RSA", fill=(255, 255, 255), anchor="mm")
    
    return img


def generate_sa_license_front(license_data: Dict[str, Any], photo_url: Optional[str] = None) -> str:
    """Generate South African driver's license front side"""
    # Standard credit card dimensions at 300 DPI
    width, height = 1012, 638
    
    # Create base image with white background
    license_img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(license_img)
    
    # Load fonts
    fonts = load_fonts()
    
    # Add security background pattern (light pink/red areas)
    security_overlay = Image.new('RGBA', (width, height), (255, 200, 200, 30))
    
    # Add pink security areas (simplified)
    security_draw = ImageDraw.Draw(security_overlay)
    security_draw.rectangle([0, 0, width//3, height], fill=(255, 150, 150, 40))
    security_draw.rectangle([width*2//3, 0, width, height//2], fill=(255, 150, 150, 40))
    
    license_img = Image.alpha_composite(license_img.convert('RGBA'), security_overlay).convert('RGB')
    draw = ImageDraw.Draw(license_img)
    
    # Add border
    draw.rectangle([5, 5, width-5, height-5], outline=(0, 0, 0), width=2)
    
    # Header section
    header_y = 30
    
    # Add coat of arms (top left)
    coat_of_arms = create_sa_coat_of_arms((50, 50))
    license_img.paste(coat_of_arms, (20, header_y - 10), coat_of_arms)
    
    # Title
    draw.text((width//2, header_y), "DRIVING LICENCE", fill=(0, 0, 0), font=fonts["title"], anchor="mm")
    draw.text((width//2, header_y + 25), "REPUBLIC OF SOUTH AFRICA", fill=(0, 0, 0), font=fonts["small"], anchor="mm")
    
    # Photo section (left side)
    photo_x, photo_y = 30, 100
    photo_width, photo_height = 140, 180
    
    # Process and add photo
    photo = download_and_process_photo(photo_url, (photo_width, photo_height))
    if photo:
        license_img.paste(photo, (photo_x, photo_y))
    else:
        # Photo placeholder
        draw.rectangle([photo_x, photo_y, photo_x + photo_width, photo_y + photo_height], 
                      outline=(0, 0, 0), width=2, fill=(240, 240, 240))
        draw.text((photo_x + photo_width//2, photo_y + photo_height//2), "PHOTO", 
                 fill=(100, 100, 100), font=fonts["regular"], anchor="mm")
    
    # Photo border
    draw.rectangle([photo_x, photo_y, photo_x + photo_width, photo_y + photo_height], 
                  outline=(0, 0, 0), width=2)
    
    # Signature area below photo
    sig_y = photo_y + photo_height + 10
    draw.rectangle([photo_x, sig_y, photo_x + photo_width, sig_y + 40], 
                  outline=(0, 0, 0), width=1)
    draw.text((photo_x + 5, sig_y + 5), "Signature:", fill=(0, 0, 0), font=fonts["tiny"])
    
    # Personal details section (right side)
    details_x = photo_x + photo_width + 30
    details_y = 100
    line_height = 25
    
    # License details
    details = [
        ("Licence No:", license_data.get('license_number', 'N/A')),
        ("Surname:", license_data.get('last_name', 'N/A')),
        ("Names:", license_data.get('first_name', 'N/A')),
        ("ID Number:", license_data.get('id_number', 'N/A')),
        ("Date of Birth:", str(license_data.get('date_of_birth', 'N/A'))),
        ("Issue Date:", str(license_data.get('issue_date', 'N/A'))),
        ("Expiry Date:", str(license_data.get('expiry_date', 'N/A'))),
        ("Category:", license_data.get('category', 'N/A')),
    ]
    
    current_y = details_y
    for label, value in details:
        draw.text((details_x, current_y), label, fill=(0, 0, 0), font=fonts["small"])
        draw.text((details_x + 100, current_y), str(value), fill=(0, 0, 0), font=fonts["regular"])
        current_y += line_height
    
    # Add restrictions if any
    if license_data.get('restrictions'):
        current_y += 10
        draw.text((details_x, current_y), "Restrictions:", fill=(0, 0, 0), font=fonts["small"])
        current_y += 15
        
        # Wrap long restriction text
        restriction_text = license_data.get('restrictions', '')
        wrapped_text = textwrap.fill(restriction_text, width=30)
        for line in wrapped_text.split('\n'):
            draw.text((details_x, current_y), line, fill=(0, 0, 0), font=fonts["tiny"])
            current_y += 12
    
    # Add watermark
    watermark = create_watermark_pattern(width, height)
    license_img = Image.alpha_composite(license_img.convert('RGBA'), watermark).convert('RGB')
    
    # Add holographic security strip (right edge)
    security_strip_x = width - 30
    for i in range(0, height, 10):
        color = (200 + (i % 55), 150 + (i % 105), 255)
        draw.rectangle([security_strip_x, i, width - 5, i + 5], fill=color)
    
    # Convert to base64
    buffer = io.BytesIO()
    license_img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_str


def generate_sa_license_back(license_data: Dict[str, Any]) -> str:
    """Generate South African driver's license back side"""
    # Standard credit card dimensions at 300 DPI
    width, height = 1012, 638
    
    # Create base image
    license_img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(license_img)
    
    # Load fonts
    fonts = load_fonts()
    
    # Add security background
    security_overlay = Image.new('RGBA', (width, height), (255, 200, 200, 30))
    license_img = Image.alpha_composite(license_img.convert('RGBA'), security_overlay).convert('RGB')
    draw = ImageDraw.Draw(license_img)
    
    # Add border
    draw.rectangle([5, 5, width-5, height-5], outline=(0, 0, 0), width=2)
    
    # Header
    draw.text((30, 30), "DRIVER RESTRICTIONS", fill=(0, 0, 0), font=fonts["large"])
    draw.text((30, 55), "Artificial Limb/Mechanical Aids", fill=(0, 0, 0), font=fonts["small"])
    
    # License categories section
    categories_y = 100
    draw.text((30, categories_y), "LICENCE CATEGORIES", fill=(0, 0, 0), font=fonts["regular"])
    
    # Define license categories with descriptions
    categories = [
        ("A", "Motorcycles"),
        ("A1", "Motorcycles ≤ 125cc"),
        ("B", "Light motor vehicles ≤ 3500kg"),
        ("C1", "Medium trucks 3500-16000kg"),
        ("C", "Heavy trucks > 16000kg"),
        ("EB", "Light trailers with B"),
        ("EC", "Heavy trailers with C")
    ]
    
    # Draw categories in a grid
    cat_start_y = categories_y + 30
    col1_x, col2_x = 30, 300
    
    for i, (cat, desc) in enumerate(categories):
        x = col1_x if i < 4 else col2_x
        y = cat_start_y + (i % 4) * 30
        
        # Category box
        draw.rectangle([x, y, x + 25, y + 20], outline=(0, 0, 0), width=1)
        draw.text((x + 12, y + 10), cat, fill=(0, 0, 0), font=fonts["small"], anchor="mm")
        
        # Description
        draw.text((x + 35, y + 10), desc, fill=(0, 0, 0), font=fonts["tiny"], anchor="lm")
    
    # Fingerprint area (bottom left)
    fingerprint_x, fingerprint_y = 50, height - 180
    fingerprint_size = 120
    
    draw.rectangle([fingerprint_x, fingerprint_y, fingerprint_x + fingerprint_size, 
                   fingerprint_y + fingerprint_size], outline=(0, 0, 0), width=2)
    
    # Create fingerprint pattern
    for i in range(5, fingerprint_size - 5, 3):
        for j in range(5, fingerprint_size - 5, 3):
            if (i + j) % 6 < 3:
                draw.point((fingerprint_x + i, fingerprint_y + j), fill=(0, 0, 0))
    
    draw.text((fingerprint_x + fingerprint_size//2, fingerprint_y + fingerprint_size + 10), 
             "RIGHT THUMB", fill=(0, 0, 0), font=fonts["tiny"], anchor="mm")
    
    # Barcode area (right side)
    barcode_x = width - 200
    barcode_y = 100
    barcode_width = 150
    barcode_height = height - 200
    
    # Generate barcode pattern
    barcode_data = f"{license_data.get('license_number', '')}{license_data.get('id_number', '')}"
    
    # Create simple barcode pattern
    for i in range(0, barcode_height, 2):
        bar_width = 1 if (hash(barcode_data + str(i)) % 3) == 0 else 3
        draw.rectangle([barcode_x, barcode_y + i, barcode_x + bar_width, barcode_y + i + 1], 
                      fill=(0, 0, 0))
    
    # Add QR code
    qr_data = {
        "license_number": license_data.get('license_number'),
        "id_number": license_data.get('id_number'),
        "category": license_data.get('category'),
        "expiry_date": license_data.get('expiry_date')
    }
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=1)
    qr.add_data(json.dumps(qr_data, default=serialize_date))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Paste QR code
    qr_pos = (barcode_x + 30, barcode_y + barcode_height - 100)
    license_img.paste(qr_img, qr_pos)
    
    # Add watermark
    watermark = create_watermark_pattern(width, height)
    license_img = Image.alpha_composite(license_img.convert('RGBA'), watermark).convert('RGB')
    
    # Authority information
    draw.text((width//2, height - 30), "Department of Transport - Republic of South Africa", 
             fill=(0, 0, 0), font=fonts["tiny"], anchor="mm")
    
    # Convert to base64
    buffer = io.BytesIO()
    license_img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_str


def generate_watermark_template(width=1012, height=638, text="SOUTH AFRICA") -> str:
    """Generate a standalone watermark template"""
    watermark = create_watermark_pattern(width, height, text)
    
    # Convert to base64
    buffer = io.BytesIO()
    watermark.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_str


# Legacy functions for backward compatibility
def generate_license_qr_code(license_data: Dict[str, Any]) -> str:
    """Generate a QR code containing license information (legacy function)"""
    json_data = json.dumps(license_data, default=serialize_date)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_str


def generate_license_barcode_data(license_number: str, id_number: str) -> str:
    """Generate barcode data for a license (legacy function)"""
    return f"{license_number.replace('-', '')}:{id_number}"


def generate_license_preview(license_data: Dict[str, Any], photo_url: Optional[str] = None) -> str:
    """Generate license preview (legacy function - now uses SA front template)"""
    return generate_sa_license_front(license_data, photo_url)