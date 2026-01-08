from PIL import Image
import os
import re
from pathlib import Path
from typing import Tuple, Optional

# Supported image formats for batch operations
SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}

def get_smart_ratio(image_path):
    """
    Calculates the closest standard aspect ratio for the given image.
    Returns string format "W:H" (e.g., "16:9").
    """
    with Image.open(image_path) as img:
        w, h = img.size
        # If w or h is 0, avoid division by zero (unlikely for valid image)
        if h == 0: return "1:1" 
        
        target = w / h
        # Official Imagen 3 / Gemini Ratios
        common = [
            (1, 1), (16, 9), (9, 16), (4, 3), (3, 4), 
            (3, 2), (2, 3), (5, 4), (4, 5), (21, 9)
        ]
        best = min(common, key=lambda r: abs(target - r[0]/r[1]))
        return f"{best[0]}:{best[1]}"


def is_supported_image(filepath: str) -> bool:
    """
    Check if file is a supported image format.
    
    Args:
        filepath: Path to file
        
    Returns:
        True if file is a supported image
    """
    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_IMAGE_FORMATS


def parse_resolution(resolution_str: str) -> Optional[Tuple[int, int]]:
    """
    Parse resolution string in format "WIDTHxHEIGHT".
    
    Args:
        resolution_str: Resolution string (e.g., "3840x2160")
        
    Returns:
        Tuple of (width, height) or None if invalid
    """
    if not resolution_str or not resolution_str.strip():
        return None
    
    pattern = r'^(\d+)\s*[xX×]\s*(\d+)$'
    match = re.match(pattern, resolution_str.strip())
    
    if not match:
        return None
    
    width = int(match.group(1))
    height = int(match.group(2))
    
    if width <= 0 or height <= 0 or width > 50000 or height > 50000:
        return None
    
    return (width, height)


def validate_resolution(resolution_str: str) -> Tuple[bool, str]:
    """
    Validate resolution string format and range.
    
    Args:
        resolution_str: Resolution string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not resolution_str or not resolution_str.strip():
        return False, "Resolution cannot be empty"
    
    result = parse_resolution(resolution_str)
    
    if result is None:
        return False, "Invalid format. Use: WIDTHxHEIGHT (e.g., 3840x2160)"
    
    return True, ""


def get_mime_type(file_path) -> str:
    """
    Get MIME type for image file based on extension.
    
    Args:
        file_path: Path to image file (Path object or string)
        
    Returns:
        MIME type string (e.g., 'image/png', 'image/jpeg')
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp'
    }
    return mime_map.get(file_path.suffix.lower(), 'image/png')


def clean_stem(stem: str) -> str:
    """
    Remove common suffixes like '_optimized' from filename stems.
    
    Args:
        stem: Filename stem to clean
        
    Returns:
        Cleaned stem without suffixes
    """
    return stem.replace("_optimized", "")


def clean_prompt_title(title: str) -> str:
    """
    Clean prompt title for filename usage.
    Removes '_+_' and ' + ' patterns and replaces with '+'.
    
    Args:
        title: Prompt title to clean
        
    Returns:
        Cleaned title suitable for filenames
    """
    # Replace "_+_" or " + " with "+" to save space but keep readability
    cleaned = title.replace("_+_", "+").replace(" + ", "+")
    # Remove any double underscores
    cleaned = re.sub(r'_{2,}', '_', cleaned)
    return cleaned
