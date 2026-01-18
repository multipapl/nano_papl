import pytest
from PySide6.QtCore import Qt
from ui.pages.settings_page import SettingsInterface
from core.utils import config_helper

def test_settings_initialization(qtbot):
    """Перевірка ініціалізації сторінки налаштувань."""
    settings = SettingsInterface(config_helper.config_manager)
    qtbot.addWidget(settings)
    
    assert settings.objectName() == "SettingsInterface"
    # Перевірка наявності основних елементів
    assert hasattr(settings, "api_key_input")
    assert hasattr(settings, "theme_card")

def test_save_api_key_ui(qtbot):
    """Verify that saving the API key through the UI updates the config."""
    settings = SettingsInterface(config_helper.config_manager)
    qtbot.addWidget(settings)
    
    test_key = "test-gemini-key-999" # Different from previous to be sure
    settings.api_key_input.setText(test_key)
    
    # Find Save Key button in api_key_card
    save_btn = None
    for i in range(settings.api_key_card.viewLayout.count()):
        widget = settings.api_key_card.viewLayout.itemAt(i).widget()
        if widget and hasattr(widget, "text") and "Save Key" in widget.text():
            save_btn = widget
            break
            
    assert save_btn is not None
    qtbot.mouseClick(save_btn, Qt.LeftButton)
    
    # Verify it saved to (isolated) config
    assert config_helper.get_value("api_key") == test_key
