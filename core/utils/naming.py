import time
import re
from pathlib import Path
from core.utils import image_utils

def generate_filename(original_stem: str, prompt_title: str, extension: str = "") -> str:
    """
    Generates a standardized filename for generated images.
    
    Format:
    {CleanOriginalStem}_{CleanPromptTitle}_{Timestamp}{Extension}
    
    Example:
    Input: "KP_View001_optimized", "Winter + Daylight", ".png"
    Output: "KP_View001_Winter+Daylight_1740003322.png"
    """
    
    # 1. Clean Original Stem (remove _optimized suffix)
    clean_stem = image_utils.clean_stem(original_stem)
    
    # 2. Clean Prompt Title
    clean_title = image_utils.clean_prompt_title(prompt_title)
    
    # 3. Timestamp
    timestamp = int(time.time())
    
    # 4. Construct
    filename = f"{clean_stem}_{clean_title}_{timestamp}"
    
    if extension:
        if not extension.startswith('.'):
            extension = f".{extension}"
        filename += extension
        
    return filename
