import pytest
import io
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image
from core.services.generation_service import GenerationService

@pytest.fixture
def service():
    return GenerationService(api_key="test-api-key")

@patch("google.genai.Client")
def test_generation_service_init(mock_client_cls):
    """Verify service initializes with API key and creates client."""
    service = GenerationService(api_key="key-123")
    assert service.api_key == "key-123"
    mock_client_cls.assert_called_once_with(api_key="key-123")

@patch("PIL.Image.open")
@patch("core.utils.image_utils.get_mime_type")
def test_generate_image_flow(mock_mime, mock_img_open, service):
    """Verify the end-to-end generate_image flow with AI client mocks."""
    # 1. Mock source image
    mock_src_img = MagicMock(spec=Image.Image)
    mock_src_img.size = (1000, 1000)
    mock_src_img.format = "PNG"
    mock_img_open.return_value.__enter__.return_value = mock_src_img
    
    # 2. Mock MIME type
    mock_mime.return_value = "image/png"
    
    # 3. Mock AI Client and Response
    service.client = MagicMock()
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake-generated-image-bytes"
    mock_response.parts = [mock_part]
    service.client.models.generate_content.return_value = mock_response
    
    # 4. Mock _save_generated_image to isolate it
    with patch.object(service, "_save_generated_image") as mock_save:
        mock_save.return_value = {"success": True, "saved_path": Path("/out/cat.png")}
        
        prompt_data = {"prompt": "A cute cat", "title": "Cat"}
        out_config = {"resolution": "2K", "ratio": "16:9", "project_out_dir": Path("/out")}
        
        result = service.generate_image(prompt_data, Path("in.png"), out_config)
        
        assert result["success"] is True
        assert result["saved_path"] == Path("/out/cat.png")
        service.client.models.generate_content.assert_called_once()
        mock_save.assert_called_once()

@patch("PIL.Image.open")
def test_save_generated_image_logic(mock_img_open, service, tmp_path):
    """Verify resolution checking and filename construction during save."""
    # 1. Mock generated image from bytes
    mock_gen_img = MagicMock(spec=Image.Image)
    mock_gen_img.size = (2048, 1152) # 2K 16:9
    mock_img_open.return_value = mock_gen_img
    
    prompt_data = {"prompt": "A cat", "title": "Great Cat"}
    source_path = Path("my_photo.png")
    out_dir = tmp_path / "output"
    config = {"project_out_dir": out_dir, "format": "PNG"}
    input_size = (1024, 576) # Source was smaller
    
    result = service._save_generated_image(b"fake-data", prompt_data, source_path, config, input_size)
    
    assert result["success"] is True
    assert result["is_diff_resolution"] is True # 2048 != 1024
    
    # Check folder structure
    expected_path = out_dir / "my_photo" / "my_photo_GreatCat" # Partial check
    assert str(result["saved_path"]).replace("\\", "/").startswith(str(out_dir).replace("\\", "/"))
    assert "_diff" in result["saved_path"].name
    assert result["saved_path"].suffix == ".png"
    
    mock_gen_img.save.assert_called_once()
