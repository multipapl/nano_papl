import json
import os
import keyring

CONFIG_FILE = "config.json"
SERVICE_NAME = "NanoPapl"
KEY_NAME = "api_key"

def save_config(data):
    """Зберігає словник з налаштуваннями у файл."""
    # Filter out sensitive keys before saving to JSON
    safe_data = data.copy()
    if KEY_NAME in safe_data:
        del safe_data[KEY_NAME]
        
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(safe_data, f, indent=4, ensure_ascii=False)

def load_config():
    """Завантажує налаштування. Якщо файлу немає — повертає порожній словник."""
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}
            
    # Migration Check: If API key is still in JSON, move to Keyring
    if KEY_NAME in config and config[KEY_NAME]:
        key_val = config[KEY_NAME]
        set_value(KEY_NAME, key_val) # This writes to keyring and removes from JSON via save_config
        # Reload to get clean state
        if KEY_NAME in config: del config[KEY_NAME]
        
    return config

def get_value(key, default=None):
    """Повертає конкретне значення за ключем."""
    # Special handling for API Key
    if key == KEY_NAME:
        try:
            val = keyring.get_password(SERVICE_NAME, KEY_NAME)
            if val: return val
        except Exception:
            pass # Fallback to config if keyring fails?
            
    config = load_config()
    # Fallback: check config (handling migration edge case where it wasn't stripped yet)
    if key == KEY_NAME and key in config:
        return config[key]
        
    return config.get(key, default)

def set_value(key, value):
    """Оновлює або додає один параметр у конфіг."""
    # Special handling for API Key
    if key == KEY_NAME:
        try:
            keyring.set_password(SERVICE_NAME, KEY_NAME, value)
            # Remove from JSON if exists
            config = load_config()
            if KEY_NAME in config:
                save_config(config) # save_config filters it out
            return
        except Exception as e:
            print(f"Keyring Error: {e}")
            # Fallback? No, better warn? For now let's just proceed.

    config = load_config()
    config[key] = value
    save_config(config)