from PIL import Image

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
