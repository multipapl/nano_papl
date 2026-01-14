import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from core.services.comfy_orchestrator import ComfyOrchestrator

@pytest.fixture
def mock_settings():
    return {
        "comfy_url": "http://localhost:8188",
        "workflow_path": "wf.json",
        "input_path": "/in",
        "output_path": "/out",
        "resolution": "2K",
        "ratio": "16:9"
    }

@pytest.fixture
def orchestrator(mock_settings):
    with patch("core.services.comfy_orchestrator.ComfyAPI"):
        return ComfyOrchestrator(mock_settings)

@patch("builtins.open")
@patch("core.services.comfy_orchestrator.PathProvider")
@patch("core.utils.prompt_parser.parse_markdown_prompts")
def test_process_batch_live_flow(mock_parse, mock_provider_cls, mock_open, orchestrator):
    """Verify live generation flow: upload -> queue -> wait -> download."""
    # 1. Setup Mock Workflow
    workflow_json = {
        "10": {"inputs": {"image": ""}},
        "20": {"inputs": {"prompt": "", "resolution": "", "aspect_ratio": "", "seed": 0}},
        "30": {"inputs": {"filename_prefix": ""}}
    }
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(workflow_json)
    orchestrator.node_mapping = {"LOAD_IMAGE": "10", "GEMINI_PROMPT": "20", "SAVE_IMAGE": "30"}
    
    # 2. Setup Task
    task = {
        "project": Path("/in/P1"), 
        "image": Path("/in/P1/i1.png"), 
        "prompt": {"title": "T1", "prompt": "P1"}
    }
    
    # 3. Setup API Mocks
    orchestrator.api.upload_image.return_value = "uploaded_name.png"
    orchestrator.api.queue_prompt.return_value = "prompt_id_123"
    orchestrator.api.get_history.return_value = {
        "prompt_id_123": {
            "outputs": {
                "30": {"images": [{"filename": "out.png"}]}
            }
        }
    }
    
    with patch("pathlib.Path.mkdir"), \
         patch.object(orchestrator, "_download_and_save") as mock_download:
        
        # We pass the template as dict
        orchestrator._process_single_task(task, 0, 1, workflow_json, Path("/out"))
        
        # Verify Flow
        orchestrator.api.upload_image.assert_called_once()
        orchestrator.api.queue_prompt.assert_called_once()
        mock_download.assert_called_once()

@patch("builtins.open")
@patch("core.services.comfy_orchestrator.PathProvider")
@patch("core.utils.prompt_parser.parse_markdown_prompts")
@patch("pathlib.Path.iterdir", autospec=True)
@patch("pathlib.Path.exists", autospec=True)
@patch("pathlib.Path.mkdir")
def test_process_batch_scanning(mock_mkdir, mock_exists, mock_iterdir, mock_parse, mock_provider_cls, mock_open, orchestrator):
    """Verify scanning logic and task creation."""
    # 1. Mocks
    mock_open.return_value.__enter__.return_value.read.return_value = '{"inputs": {}}'
    
    # Mock PathProvider methods to return specific Paths
    mock_provider = mock_provider_cls.return_value
    mock_provider.get_default_projects_path.return_value = Path("/in")
    mock_provider.get_prompts_file.return_value = Path("/in/prompts.md")
    mock_provider.get_optimized_dir.return_value = Path("/in/optimized")
    
    def get_path_str(args):
        if not args: return ""
        # With autospec=True, args[0] is the Path instance
        return str(args[0]).replace("\\", "/")

    def exists_side_effect(*args, **kwargs):
        p_str = get_path_str(args)
        # Single project mode detection
        if p_str == "/in/prompts.md": return True
        # Optimized dir should not exist in this test
        if "/optimized" in p_str: return False
        return True
    mock_exists.side_effect = exists_side_effect
    
    def iterdir_side_effect(*args, **kwargs):
        p_str = get_path_str(args)
        # Scan /in
        if p_str == "/in":
            img = MagicMock(spec=Path)
            img.suffix = ".png"
            img.name = "img1.png"
            img.stem = "img1"
            img.is_file.return_value = True
            return [img]
        return []
    mock_iterdir.side_effect = iterdir_side_effect
    
    mock_parse.return_value = [{"title": "T1", "prompt": "P1"}]
    
    # We mock _process_single_task to avoid API calls in this test
    with patch.object(orchestrator, "_process_single_task") as mock_process:
        orchestrator.process_batch()
        assert mock_process.called
        assert mock_process.call_count == 1
