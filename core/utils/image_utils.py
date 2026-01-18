from PIL import Image
import os
import re
import hashlib
from pathlib import Path
from typing import Tuple, Optional, Union
from core.utils.path_provider import PathProvider

# Supported image formats for batch operations
SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}

from core.config.resolutions import RESOLUTION_TABLE

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
        # Get ratios from the central truth table
        common = []
        for ratio_str in RESOLUTION_TABLE.keys():
            try:
                rw, rh = map(int, ratio_str.split(':'))
                common.append((rw, rh))
            except ValueError:
                continue

        if not common:
            # Fallback to standard 10 if table parsing fails
            common = [(1, 1), (16, 9), (9, 16), (4, 3), (3, 4), (3, 2), (2, 3), (5, 4), (4, 5), (21, 9)]

        best = min(common, key=lambda r: abs(target - r[0]/r[1]))
        return f"{best[0]}:{best[1]}"

def get_or_create_thumbnail(image_path: Union[str, Path], target_width: int = 400) -> str:
    """
    Returns the path to a cached thumbnail of the image.
    Generates it if it doesn't exist.
    
    Args:
        image_path: Path to original source image
        target_width: Desired thumbnail width (preserves aspect ratio)
        
    Returns:
        Path to the thumbnail file as a string
    """
    if isinstance(image_path, str):
        image_path = Path(image_path)
    
    if not image_path.exists():
        return str(image_path) # Fallback to original path if it doesn't exist
    
    try:
        # Create a unique hash for the cache filename
        # Combine path and modification time to handle file updates
        mtime = os.path.getmtime(image_path)
        cache_key = f"{image_path.absolute()}_{mtime}_{target_width}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        cache_dir = PathProvider().get_thumbnails_dir()
        thumb_path = cache_dir / f"{cache_hash}.jpg"
        
        # If cached version exists, return it
        if thumb_path.exists():
            return str(thumb_path)
            
        # Otherwise, generate thumbnail
        with Image.open(image_path) as img:
            # Calculate height to maintain aspect ratio
            w, h = img.size
            if w == 0: return str(image_path)
            
            ratio = target_width / w
            target_height = int(h * ratio)
            
            # Use high-quality resampling (LANCZOS or Resampling.LANCZOS depending on PIL version)
            try:
                resample_method = Image.Resampling.LANCZOS
            except AttributeError:
                resample_method = Image.LANCZOS
                
            thumb_img = img.resize((target_width, target_height), resample_method)
            
            # Save as JPEG with moderate quality to save space/I/O
            if thumb_img.mode in ("RGBA", "P"):
                thumb_img = thumb_img.convert("RGB")
            
            thumb_img.save(thumb_path, "JPEG", quality=85, optimize=True)
            
        return str(thumb_path)
        
    except Exception as e:
        import logging
        logging.error(f"Failed to create thumbnail for {image_path}: {e}")
        return str(image_path) # Fallback to original

def save_image_with_format(image: Image.Image, save_path: Path, target_format: str, quality: int = 95) -> None:
    """
    Standardized helper to save PIL images with format handling.
    
    Args:
        image: PIL Image object
        save_path: Destination Path
        target_format: 'PNG' or 'JPG'
        quality: JPEG compression quality
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    if target_format.upper() == "JPG":
        # Ensure RGB mode for JPEG (no alpha)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(save_path, "JPEG", quality=quality, optimize=True)
    else:
        # Default to PNG
        image.save(save_path, "PNG", optimize=True)

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
