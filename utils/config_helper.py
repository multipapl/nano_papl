import json
import os

CONFIG_FILE = "config.json"

def save_config(data):
    """Зберігає словник з налаштуваннями у файл."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_config():
    """Завантажує налаштування. Якщо файлу немає — повертає порожній словник."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def get_value(key, default=None):
    """Повертає конкретне значення за ключем."""
    config = load_config()
    return config.get(key, default)

def set_value(key, value):
    """Оновлює або додає один параметр у конфіг."""
    config = load_config()
    config[key] = value
    save_config(config)