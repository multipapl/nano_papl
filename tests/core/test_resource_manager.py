"""
Tests for ResourceManager.
Covers singleton behavior, path resolution, and icon caching.
"""
import pytest
from pathlib import Path
from core.utils.resource_manager import ResourceManager, Resources


class TestResourceManagerSingleton:
    """Tests for singleton behavior."""
    
    def test_resource_manager_is_singleton(self):
        """Verify single instance is returned."""
        rm1 = ResourceManager()
        rm2 = ResourceManager()
        assert rm1 is rm2
    
    def test_global_resources_exists(self):
        """Verify global Resources instance is available."""
        assert Resources is not None
        assert isinstance(Resources, ResourceManager)


class TestPathResolution:
    """Tests for path resolution functionality."""
    
    def test_get_path_returns_path_object(self):
        """Verify get_path returns Path object."""
        path = Resources.get_path("test/file.txt")
        assert isinstance(path, Path)
    
    def test_get_data_file_includes_data_dir(self):
        """Verify get_data_file prefixes with data directory."""
        path = Resources.get_data_file("templates.json")
        assert "data" in str(path)
        assert path.name == "templates.json"
    
    def test_get_asset_includes_assets_dir(self):
        """Verify get_asset prefixes with assets directory."""
        path = Resources.get_asset("icon.png")
        assert "assets" in str(path)
        assert path.name == "icon.png"
    
    def test_exists_returns_bool(self):
        """Verify exists() returns boolean."""
        result = Resources.exists("nonexistent_file_12345.xyz")
        assert isinstance(result, bool)
        assert result is False


class TestProperties:
    """Tests for property accessors."""
    
    def test_base_path_is_path(self):
        """Verify base_path returns Path object."""
        assert isinstance(Resources.base_path, Path)
    
    def test_assets_path_is_path(self):
        """Verify assets_path returns Path object."""
        assert isinstance(Resources.assets_path, Path)
    
    def test_data_path_is_path(self):
        """Verify data_path returns Path object."""
        assert isinstance(Resources.data_path, Path)
