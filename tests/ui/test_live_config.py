import pytest
import os
import json
from PySide6.QtCore import Qt
from ui.pages.settings_page import SettingsInterface
from core.utils import config_helper

def test_settings_save_to_disk(qtbot, tmp_path, monkeypatch):
    """Перевірка, чи дійсно натискання кнопки Save зберігає дані у файл."""
    # Налаштовуємо тимчасовий конфіг-файл
    config_file = tmp_path / "config.json"
    monkeypatch.setattr(config_helper, "CONFIG_FILE", str(config_file))
    
    # Створюємо інтерфейс
    settings = SettingsInterface()
    qtbot.addWidget(settings)
    
    # 1. Тестуємо збереження ComfyUI URL (він точно йде в JSON)
    test_url = "http://localhost:8188"
    settings.comfy_url_input.setText(test_url)
    
    # Клікаємо Save URL
    # В comfy_url_card кнопка Save є другим віджетом
    save_btn = settings.comfy_url_card.viewLayout.itemAt(1).widget()
    qtbot.mouseClick(save_btn, Qt.LeftButton)
    
    # Перевіряємо файл на диску
    # Оскільки ми використовуємо config_helper.set_value, він має створити файл
    assert os.path.exists(config_file)
    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["comfy_url"] == test_url
        
    # 2. Тестуємо збереження кольору теми
    # Колір точно записується в JSON
    test_color = "#ff0000"
    from PySide6.QtGui import QColor
    settings.on_color_changed(QColor(test_color))
    
    # Перевіряємо файл на диску
    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Тепер використовуємо єдиний ключ theme_color
        assert data["theme_color"] == test_color
