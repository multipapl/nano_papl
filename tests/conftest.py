import pytest
import os
import sys

# Додаємо корінь проекту в sys.path, щоб модулі були доступні для імпорту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """
    Global fixture to isolate tests from the real application state.
    - Redirects CONFIG_FILE and PRESETS_FILE to a temporary directory.
    - Mocks the keyring to prevent accidental API key overwrites.
    - Resets the internal API key cache.
    """
    from core.utils import config_helper
    import keyring
    
    # 1. Create temp config files
    test_config_dir = tmp_path / "nano_papl_tests"
    test_config_dir.mkdir(parents=True, exist_ok=True)
    test_config_file = test_config_dir / "config.json"
    test_presets_file = test_config_dir / "presets.json"
    
    # 2. Redirect paths in config_helper
    monkeypatch.setattr(config_helper, "CONFIG_FILE", str(test_config_file))
    monkeypatch.setattr(config_helper, "PRESETS_FILE", str(test_presets_file))
    monkeypatch.setattr(config_helper, "APP_DATA_DIR", str(test_config_dir))
    
    # 3. Reset internal cache and FORCE RELOAD with new paths
    config_helper._API_KEY_CACHE = None
    config_helper.config_manager.reload()
    
    # 4. Mock keyring GLOBALLY for all tests
    mock_keyring = {}
    
    def mock_set_password(service, username, password):
        mock_keyring[f"{service}:{username}"] = password
        
    def mock_get_password(service, username):
        return mock_keyring.get(f"{service}:{username}")
        
    monkeypatch.setattr(keyring, "set_password", mock_set_password)
    monkeypatch.setattr(keyring, "get_password", mock_get_password)
    
    yield
    
    # Cleanup cache again after test
    config_helper._API_KEY_CACHE = None

@pytest.fixture
def mock_config(tmp_path):
    """Fixture for a custom temporary configuration folder (if needed)."""
    config_dir = tmp_path / "custom_config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

@pytest.fixture
def sample_history():
    """Sample chat history data for testing."""
    return [
        {"role": "user", "text": "Hello"},
        {"role": "model", "text": "Hi there! How can I help you today?"}
    ]
