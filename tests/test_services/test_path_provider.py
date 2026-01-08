import os
import pytest
from pathlib import Path
from core.utils.path_provider import PathProvider

def test_singleton_pattern():
    """Verify PathProvider is a singleton."""
    p1 = PathProvider()
    p2 = PathProvider()
    assert p1 is p2
    assert p1.app_root == p2.app_root

def test_app_root_exists():
    """Verify app root is set and exists."""
    provider = PathProvider()
    assert provider.get_app_root().exists()

def test_default_projects_path():
    """Verify documents directory logic."""
    provider = PathProvider()
    docs = provider.get_default_projects_path()
    # It should be under Documents/NanoPapl
    assert "NanoPapl" in str(docs)

def test_subdirectories(tmp_path):
    """Verify helper methods for subdirectories."""
    provider = PathProvider()
    project_path = tmp_path / "MyProject"
    
    renders = provider.get_renders_dir(project_path)
    assert renders == project_path / "_renders"
    
    optimized = provider.get_optimized_dir(project_path)
    assert optimized == project_path / "optimized"
    
    prompts = provider.get_prompts_file(project_path)
    assert prompts == project_path / "prompts.md"

def test_temp_dir():
    """Verify temp dir creation."""
    provider = PathProvider()
    temp = provider.get_temp_dir()
    assert temp.exists()
    assert temp.name == "temp"
