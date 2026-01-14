import pytest
import os
import sys

# Додаємо корінь проекту в sys.path, щоб модулі були доступні для імпорту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_config(tmp_path):
    """Фікстура для тимчасового файлу конфігурації."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def sample_history():
    """Приклад даних історії повідомлень."""
    return [
        {"role": "user", "content": "Привіт"},
        {"role": "assistant", "content": "Вітаю! Чим можу допомогти?"}
    ]
