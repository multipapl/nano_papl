import pytest
import os
import json
from unittest.mock import MagicMock, patch
from core.utils import config_helper

@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the internal cache of config_helper before each test."""
    config_helper._API_KEY_CACHE = None

def test_get_value_standard(tmp_path, monkeypatch):
    """Verify loading standard values from JSON config."""
    config_file = tmp_path / "config_test.json"
    config_data = {"data_root": "C:/MockPath", "theme": "Dark"}
    config_file.write_text(json.dumps(config_data))
    
    monkeypatch.setattr(config_helper, "CONFIG_FILE", str(config_file))
    config_helper.config_manager.reload()
    
    assert config_helper.get_value("data_root") == "C:/MockPath"
    assert config_helper.get_value("theme") == "Dark"
    assert config_helper.get_value("non_existent", "default") == "default"

def test_set_value_standard(tmp_path, monkeypatch):
    """Verify saving standard values to JSON config."""
    config_file = tmp_path / "config_save_test.json"
    monkeypatch.setattr(config_helper, "CONFIG_FILE", str(config_file))
    config_helper.config_manager.reload()
    
    config_helper.set_value("test_key", "test_val")
    
    with open(config_file, "r") as f:
        data = json.load(f)
        assert data["test_key"] == "test_val"

@patch("core.utils.config_helper.keyring")
def test_keyring_integration(mock_keyring, tmp_path, monkeypatch):
    """Verify that sensitive keys are handled via keyring and cache."""
    config_file = tmp_path / "config_keyring.json"
    monkeypatch.setattr(config_helper, "CONFIG_FILE", str(config_file))
    config_helper.config_manager.reload()
    
    # 1. Set sensitive value
    mock_keyring.set_password.reset_mock()
    config_helper.set_value("api_key", "secret-123")
    
    mock_keyring.set_password.assert_called()
    assert config_helper._API_KEY_CACHE == "secret-123"
    
    # 2. Get sensitive value (should hit cache first)
    mock_keyring.get_password.reset_mock()
    assert config_helper.get_value("api_key") == "secret-123"
    # Should NOT call keyring because it's in cache
    assert not mock_keyring.get_password.called
    
    # 3. Get after clearing cache (should hit keyring)
    config_helper._API_KEY_CACHE = None
    mock_keyring.get_password.return_value = "secret-123"
    # We must reload to sync keyring -> model
    config_helper.config_manager.reload() 
    assert config_helper.get_value("api_key") == "secret-123"
    mock_keyring.get_password.assert_called()
