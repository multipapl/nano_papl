import pytest
import os
from unittest.mock import MagicMock, patch
from core.services.image_resizer_service import ImageResizerService

def test_calculate_proportional_size():
    """Verify proportional scaling math for different scenarios."""
    resizer = ImageResizerService(1000, 1000)
    
    # 1. Smaller than target -> No upscale
    assert resizer.calculate_proportional_size(500, 400) == (500, 400)
    
    # 2. Larger than target (Square) -> Fit to target
    assert resizer.calculate_proportional_size(2000, 2000) == (1000, 1000)
    
    # 3. Landscape -> Width constrained
    assert resizer.calculate_proportional_size(2000, 1000) == (1000, 500)
    
    # 4. Portrait -> Height constrained
    assert resizer.calculate_proportional_size(1000, 2000) == (500, 1000)

@patch("PIL.Image.open")
@patch("os.makedirs")
def test_resize_image_call(mock_makedirs, mock_img_open):
    """Verify PIL methods are called correctly for resizing."""
    mock_img = MagicMock()
    mock_img.size = (2000, 2000)
    mock_img.format = "PNG"
    mock_img_open.return_value.__enter__.return_value = mock_img
    
    # Mock resize result
    mock_resized = MagicMock()
    mock_img.resize.return_value = mock_resized
    
    resizer = ImageResizerService(1000, 1000)
    success = resizer.resize_image("in.png", "out.png")
    
    assert success is True
    mock_img.resize.assert_called_once()
    mock_resized.save.assert_called_once()

@patch("os.walk")
@patch("core.services.image_resizer_service.is_supported_image")
def test_scan_images(mock_is_supported, mock_walk):
    """Verify recursive scanning and path preparation."""
    # Mock os.walk structure
    mock_walk.return_value = [
        ("/root", ["sub"], ["img1.png", "other.txt"]),
        ("/root/sub", [], ["img2.jpg"])
    ]
    
    # Only images are supported
    mock_is_supported.side_effect = lambda p: p.endswith((".png", ".jpg"))
    
    resizer = ImageResizerService(1000, 1000)
    pairs = resizer.scan_images("/root", "/output")
    
    assert len(pairs) == 2
    # Check paths normalization (using / for cross-platform check)
    p1 = (os.path.abspath("/root/img1.png"), os.path.abspath("/output/img1.png"))
    p2 = (os.path.abspath("/root/sub/img2.jpg"), os.path.abspath("/output/sub/img2.jpg"))
    
    # verify existence in pairs
    assert any(p[0].endswith("img1.png") and p[1].endswith("img1.png") for p in pairs)
    assert any(p[0].endswith("img2.jpg") and p[1].endswith("sub/img2.jpg") or p[1].endswith("sub\\img2.jpg") for p in pairs)
