import pytest
from PySide6.QtCore import Qt
from ui.pages.settings_page import SettingsInterface
from core.utils import config_helper

def test_settings_initialization(qtbot):
    """Перевірка ініціалізації сторінки налаштувань."""
    settings = SettingsInterface()
    qtbot.addWidget(settings)
    
    assert settings.objectName() == "SettingsInterface"
    # Перевірка наявності основних елементів
    assert hasattr(settings, "api_key_input")
    assert hasattr(settings, "theme_card")

def test_save_api_key_ui(qtbot, monkeypatch):
    """Перевірка збереження API ключа через UI."""
    settings = SettingsInterface()
    qtbot.addWidget(settings)
    
    test_key = "test-gemini-key-123"
    settings.api_key_input.setText(test_key)
    
    # Симулюємо клік на кнопку збереження
    # Шукаємо кнопку Save Key в api_key_card
    save_btn = None
    for i in range(settings.api_key_card.viewLayout.count()):
        widget = settings.api_key_card.viewLayout.itemAt(i).widget()
        if widget and hasattr(widget, "text") and "Save Key" in widget.text():
            save_btn = widget
            break
            
    assert save_btn is not None
    qtbot.mouseClick(save_btn, Qt.LeftButton)
    
    # Перевіряємо чи збереглось у конфіг
    assert config_helper.get_value("api_key") == test_key
