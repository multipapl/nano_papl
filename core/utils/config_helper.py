import json
import os
import keyring
from core.logger import logger
from core.constants import (
    DEFAULT_SYSTEM_INSTRUCTION, CONFIG_FILE_NAME, PRESETS_FILE_NAME, 
    KEYRING_SERVICE_NAME, CONFIG_KEY_API_KEY
)

CONFIG_NAME = CONFIG_FILE_NAME
PRESETS_NAME = PRESETS_FILE_NAME
SERVICE_NAME = KEYRING_SERVICE_NAME
KEY_NAME = CONFIG_KEY_API_KEY

# AppData Storage
APP_DATA_DIR = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "NanoPapl")
os.makedirs(APP_DATA_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(APP_DATA_DIR, CONFIG_NAME)
PRESETS_FILE = os.path.join(APP_DATA_DIR, PRESETS_NAME)

# Memory cache to prevent redundant keyring hits and handle brief unavailabilities
_API_KEY_CACHE = None

def save_config(data):
    """Зберігає словник з налаштуваннями у файл."""
    # Filter out sensitive keys before saving to JSON
    safe_data = data.copy()
    if KEY_NAME in safe_data:
        del safe_data[KEY_NAME]
        
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(safe_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

def load_config():
    """Завантажує налаштування. Якщо файлу немає — повертає порожній словник."""
    global _API_KEY_CACHE
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}
            
    # Migration Check: If API key is still in JSON, move to Keyring and cache
    if KEY_NAME in config and config[KEY_NAME]:
        key_val = str(config[KEY_NAME]).strip()
        logger.info(f"Migrating API key from JSON to Keyring (Length: {len(key_val)})")
        
        # Update Cache
        _API_KEY_CACHE = key_val
        
        try:
            keyring.set_password(SERVICE_NAME, KEY_NAME, key_val)
            del config[KEY_NAME]
            # Save the JSON without the key
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Migration Error: {e}")
        
    return config

def get_value(key, default=None):
    """Повертає конкретне значення за ключем."""
    global _API_KEY_CACHE
    
    # Special handling for API Key
    if key == KEY_NAME:
        # 1. Try Cache First (Fastest, Safest)
        if _API_KEY_CACHE:
            # logger.debug(f"Retrieved API Key from Cache (Length: {len(_API_KEY_CACHE)})")
            return _API_KEY_CACHE
            
        # 2. Try Keyring
        try:
            val = keyring.get_password(SERVICE_NAME, KEY_NAME)
            if val:
                val = val.strip()
                _API_KEY_CACHE = val # Sync Cache
                logger.info(f"Retrieved API Key from Keyring (Length: {len(val)})")
                return val
            else:
                logger.warning("API Key NOT FOUND in Keyring.")
        except Exception as e:
            logger.error(f"Keyring retrieval error: {e}")
            
    config = load_config()
    
    # 3. Fallback: check config (handling migration edge case where it wasn't stripped yet)
    if key == KEY_NAME and key in config:
        fallback_val = str(config[key]).strip()
        if fallback_val:
            _API_KEY_CACHE = fallback_val # Sync Cache
            return fallback_val
        
    return config.get(key, default)

def set_value(key, value):
    """Оновлює або додає один параметр у конфіг."""
    global _API_KEY_CACHE
    
    # Special handling for API Key
    if key == KEY_NAME:
        val_str = str(value).strip()
        
        # Validation: Don't overwrite with empty string if we already have a key
        if not val_str and _API_KEY_CACHE:
             logger.warning("Attempted to set empty API Key while cache exists. Ignoring.")
             return

        logger.info(f"Setting API Key: Saving to Keyring and Cache (Input Length: {len(val_str)})")
        _API_KEY_CACHE = val_str # Sync Cache
        
        try:
            keyring.set_password(SERVICE_NAME, KEY_NAME, val_str)
            # Ensure it is removed from JSON if it was ever there
            config = load_config()
            if KEY_NAME in config:
                save_config(config)
            return
        except Exception as e:
            logger.error(f"Keyring Error during set_password: {e}")

    config = load_config()
    config[key] = value
    save_config(config)