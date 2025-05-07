import io
import base64
import json
from typing import Dict, Any, Optional
from datetime import date, datetime
import qrcode
from PIL import Image, ImageDraw, ImageFont


def serialize_date(obj):
    """Helper function to serialize dates to ISO format strings"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def generate_license_qr_code(license_data: Dict[str, Any]) -> str:
    """
    Generate a QR code containing license information.
    Returns a base64 encoded string of the QR code image.
    """
    # Create a JSON string of the license data
    json_data = json.dumps(license_data, default=serialize_date)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_str


def generate_license_barcode_data(license_number: str, id_number: str) -> str:
    """
    Generate barcode data for a license.
    For now, this just combines the license number and ID number.
    In a real system, this would use a specific barcode data format.
    """
    return f"{license_number.replace('-', '')}:{id_number}"


def generate_license_preview(
    license_data: Dict[str, Any],
    photo_url: Optional[str] = None
) -> str:
    """
    Generate a preview image of the license.
    Returns a base64 encoded string of the preview image.
    """
    # Create a blank image (standard credit card size, 85.60 × 53.98 mm at 300 DPI)
    width, height = 1012, 638  # Pixels for 300 DPI
    license_img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(license_img)
    
    # Add border
    draw.rectangle([10, 10, width-10, height-10], outline=(0, 0, 0), width=2)
    
    # Add title
    try:
        # Try to load a font, fall back to default if not available
        title_font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        title_font = ImageFont.load_default()
        
    try:
        # Try to load a font, fall back to default if not available
        regular_font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        regular_font = ImageFont.load_default()
        
    try:
        # Try to load a font, fall back to default if not available
        small_font = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        small_font = ImageFont.load_default()
    
    # Draw title
    draw.text((width//2, 40), "DRIVER'S LICENSE", fill=(0, 0, 0), font=title_font, anchor="mm")
    
    # Draw main content
    draw.text((30, 100), f"License No: {license_data.get('license_number', 'N/A')}", fill=(0, 0, 0), font=regular_font)
    draw.text((30, 140), f"Name: {license_data.get('first_name', '')} {license_data.get('last_name', '')}", fill=(0, 0, 0), font=regular_font)
    draw.text((30, 180), f"ID Number: {license_data.get('id_number', 'N/A')}", fill=(0, 0, 0), font=regular_font)
    draw.text((30, 220), f"Date of Birth: {license_data.get('date_of_birth', 'N/A')}", fill=(0, 0, 0), font=regular_font)
    draw.text((30, 260), f"Issue Date: {license_data.get('issue_date', 'N/A')}", fill=(0, 0, 0), font=regular_font)
    draw.text((30, 300), f"Expiry Date: {license_data.get('expiry_date', 'N/A')}", fill=(0, 0, 0), font=regular_font)
    draw.text((30, 340), f"Category: {license_data.get('category', 'N/A')}", fill=(0, 0, 0), font=regular_font)
    
    # Add placeholder for photo if no photo URL provided
    if photo_url:
        # In a real system, we'd load the photo from the URL
        # For this demo, we'll just create a placeholder
        photo_box = (width - 220, 100, width - 30, 290)
    else:
        photo_box = (width - 220, 100, width - 30, 290)
        draw.rectangle(photo_box, outline=(0, 0, 0), width=2)
        draw.text((photo_box[0] + 95, photo_box[1] + 95), "PHOTO", fill=(0, 0, 0), font=regular_font, anchor="mm")
    
    # Add restrictions and medical conditions if present
    y_pos = 380
    if license_data.get('restrictions'):
        draw.text((30, y_pos), f"Restrictions: {license_data.get('restrictions')}", fill=(0, 0, 0), font=small_font)
        y_pos += 30
    
    if license_data.get('medical_conditions'):
        draw.text((30, y_pos), f"Medical: {license_data.get('medical_conditions')}", fill=(0, 0, 0), font=small_font)
        y_pos += 30
    
    # Generate QR code for the bottom right
    qr_data = {
        "license_number": license_data.get('license_number'),
        "id_number": license_data.get('id_number'),
        "category": license_data.get('category'),
        "expiry_date": license_data.get('expiry_date')
    }
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=1,
    )
    qr.add_data(json.dumps(qr_data, default=serialize_date))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Calculate position for QR code
    qr_pos = (width - qr_img.size[0] - 30, height - qr_img.size[1] - 30)
    
    # Paste QR code onto license
    license_img.paste(qr_img, qr_pos)
    
    # Add authority information
    draw.text((width//2, height - 50), "Republic of South Africa - Department of Transport", fill=(0, 0, 0), font=small_font, anchor="mm")
    
    # Convert to base64
    buffer = io.BytesIO()
    license_img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_str 