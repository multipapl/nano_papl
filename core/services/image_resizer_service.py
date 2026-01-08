"""Image resizing service for batch operations."""
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
import os

from core.utils.image_utils import is_supported_image


class ImageResizerService:
    """
    Service for batch image resizing with proportional scaling.
    
    Handles image processing operations including:
    - Proportional scaling to fit target resolution
    - Folder structure preservation
    - Multiple format support with quality optimization
    """
    
    def __init__(self, target_width: int, target_height: int):
        """
        Initialize resizer with target resolution.
        
        Args:
            target_width: Target width in pixels
            target_height: Target height in pixels
        """
        self.target_width = target_width
        self.target_height = target_height
    
    def calculate_proportional_size(
        self, 
        original_width: int, 
        original_height: int
    ) -> Tuple[int, int]:
        """
        Calculate new size that fits within target resolution while maintaining aspect ratio.
        
        Args:
            original_width: Original image width
            original_height: Original image height
            
        Returns:
            Tuple of (new_width, new_height)
        """
        # Calculate scaling ratio - use the smaller ratio to ensure image fits within bounds
        width_ratio = self.target_width / original_width
        height_ratio = self.target_height / original_height
        scaling_ratio = min(width_ratio, height_ratio)
        
        # If image is already smaller than target, don't upscale
        if scaling_ratio >= 1.0:
            return original_width, original_height
        
        # Calculate new dimensions
        new_width = int(original_width * scaling_ratio)
        new_height = int(original_height * scaling_ratio)
        
        return new_width, new_height
    
    def resize_image(self, input_path: str, output_path: str) -> bool:
        """
        Resize image and save to output path.
        
        Args:
            input_path: Path to input image
            output_path: Path to save resized image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Open image
            with Image.open(input_path) as img:
                # Get original dimensions
                original_width, original_height = img.size
                
                # Calculate new dimensions
                new_width, new_height = self.calculate_proportional_size(
                    original_width, original_height
                )
                
                # If no resize needed, just copy
                if new_width == original_width and new_height == original_height:
                    img.save(output_path, quality=95, optimize=True)
                    return True
                
                # Resize with high-quality resampling
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Save with original format and high quality
                save_kwargs = {'optimize': True}
                
                if img.format == 'JPEG':
                    save_kwargs['quality'] = 95
                elif img.format == 'PNG':
                    save_kwargs['compress_level'] = 6
                elif img.format == 'WEBP':
                    save_kwargs['quality'] = 95
                
                resized_img.save(output_path, **save_kwargs)
                
            return True
            
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return False
    
    def scan_images(
        self, 
        input_folder: str, 
        output_folder: str,
        max_depth: int = 3
    ) -> List[Tuple[str, str]]:
        """
        Scan input folder for images and prepare output paths.
        
        Args:
            input_folder: Input folder path
            output_folder: Output folder path
            max_depth: Maximum recursion depth for subfolders
            
        Returns:
            List of tuples: [(input_path, output_path), ...]
        """
        input_folder = os.path.abspath(input_folder)
        output_folder = os.path.abspath(output_folder)
        image_pairs = []
        
        for root, dirs, files in os.walk(input_folder):
            # Calculate current depth
            relative_path = os.path.relpath(root, input_folder)
            if relative_path == '.':
                depth = 0
            else:
                depth = len(relative_path.split(os.sep))
            
            # Stop if max depth exceeded
            if depth >= max_depth:
                dirs.clear()  # Don't recurse deeper
            
            # Process image files
            for filename in files:
                input_path = os.path.join(root, filename)
                
                # Check if it's a supported image
                if is_supported_image(input_path):
                    # Calculate output path preserving folder structure
                    rel_path = os.path.relpath(input_path, input_folder)
                    output_path = os.path.join(output_folder, rel_path)
                    
                    image_pairs.append((input_path, output_path))
        
        return image_pairs
