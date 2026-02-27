import pytest
from PySide6.QtCore import Qt
from ui.pages.settings_page import SettingsInterface
from core.models import AppConfig

class MockConfigManager:
    def __init__(self):
        self.config = AppConfig()
        self.saved = False

    def save(self):
        self.saved = True

def test_settings_initialization(qtbot):
    """Перевірка ініціалізації сторінки налаштувань."""
    mock_manager = MockConfigManager()
    settings = SettingsInterface(mock_manager)
    qtbot.addWidget(settings)
    
    assert settings.objectName() == "SettingsInterface"
    # Перевірка наявності основних елементів
    assert hasattr(settings, "api_key_input")
    assert hasattr(settings, "theme_card")

def test_save_api_key_ui(qtbot):
    """Verify that saving the API key through the UI updates the config."""
    mock_manager = MockConfigManager()
    settings = SettingsInterface(mock_manager)
    qtbot.addWidget(settings)
    
    test_key = "test-gemini-key-valid-length-more-than-30-chars" # Valid length (>30)
    settings.api_key_input.setText(test_key)
    
    # Simulate save action directly to avoid UI ambiguity in headless test env
    settings.save_api_key()
    
    # Verify it saved to (isolated) config
    assert mock_manager.saved is True
    assert mock_manager.config.api_key == test_key

def test_api_visibility_toggle(qtbot):
    """Verify that the visibility toggle button changes the echo mode."""
    mock_manager = MockConfigManager()
    settings = SettingsInterface(mock_manager)
    qtbot.addWidget(settings)
    
    from qfluentwidgets import LineEdit, FluentIcon
    
    # Default should be Password
    assert settings.api_key_input.echoMode() == LineEdit.Password
    
    # Toggle to Show (Normal)
    settings.toggle_api_visibility()
    assert settings.api_key_input.echoMode() == LineEdit.Normal
    
    # Toggle back to Hide (Password)
    settings.toggle_api_visibility()
    assert settings.api_key_input.echoMode() == LineEdit.Password
