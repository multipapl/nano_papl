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

from core.models import AppConfig

# Memory cache for API key
_API_KEY_CACHE = None

class ConfigManager:
    """
    Singleton manager for application configuration using AppConfig model.
    Provides object-oriented access to settings.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = AppConfig()
            cls._instance.load()
        return cls._instance

    def load(self):
        """Loads config from file into AppConfig object."""
        global _API_KEY_CACHE
        raw_data = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
        
        # Pull API Key from keyring
        api_key = self._get_api_key_secure()
        if api_key:
            raw_data[KEY_NAME] = api_key
            _API_KEY_CACHE = api_key

        self.config = AppConfig.from_dict(raw_data)
        return self.config

    def reload(self):
        """Forces a reload of the configuration from disk."""
        return self.load()

    def save(self):
        """Saves current AppConfig object to file."""
        data = self.config.to_dict()
        
        # Securely save API Key and remove from dict
        if KEY_NAME in data:
            self._set_api_key_secure(data[KEY_NAME])
            del data[KEY_NAME]
            
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _get_api_key_secure(self):
        """Retrieves API Key from keyring or cache."""
        global _API_KEY_CACHE
        if _API_KEY_CACHE: return _API_KEY_CACHE
        try:
            val = keyring.get_password(SERVICE_NAME, KEY_NAME)
            return val.strip() if val else None
        except Exception:
            return None

    def _set_api_key_secure(self, value):
        """Saves API Key to keyring and updates cache."""
        global _API_KEY_CACHE
        val_str = str(value).strip()
        if not val_str and _API_KEY_CACHE: return
        
        _API_KEY_CACHE = val_str
        try:
            keyring.set_password(SERVICE_NAME, KEY_NAME, val_str)
        except Exception as e:
            logger.error(f"Keyring Error: {e}")

# Singleton instance
config_manager = ConfigManager()

# --- Legacy Compatibility Layer (Facilitates gradual migration) ---

def load_config():
    return config_manager.load().to_dict()

def save_config(data):
    config_manager.config = AppConfig.from_dict(data)
    config_manager.save()

def get_value(key, default=None):
    """
    Retrieves value from config object. 
    Favors specific model attributes, fallbacks to _extra dict.
    """
    config = config_manager.config
    if hasattr(config, key):
        return getattr(config, key)
    return config._extra.get(key, default)

def set_value(key, value):
    """Updates value in config object and saves."""
    config = config_manager.config
    if hasattr(config, key):
        setattr(config, key, value)
    else:
        config._extra[key] = value
    config_manager.save()
