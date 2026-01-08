import os
from pathlib import Path

# Application Metadata
APP_NAME = "NanoPapl"
APP_VERSION = "1.2.2"
WINDOW_TITLE_PREFIX = f"{APP_NAME} v{APP_VERSION} | AI Archviz Automation"

# Configuration Keys
CONFIG_KEY_API_KEY = "api_key"
CONFIG_FILE_NAME = "config.json"
PRESETS_FILE_NAME = "presets.json"
KEYRING_SERVICE_NAME = "NanoPapl"

# File Names & Paths
DEFAULT_PROMPTS_FILE = "prompts.md"
RENDERS_DIR_NAME = "_renders"
OPTIMIZED_DIR_NAME = "optimized"
ASSETS_DIR_NAME = "assets"
ICON_FILENAME = "icon.png"

# Default Values
DEFAULT_COMFY_URL = "http://127.0.0.1:8188"
DEFAULT_SYSTEM_INSTRUCTION = (
    "You are a Senior Architectural Visualization Art Director. "
    "Critique images strictly on lighting, composition, materials, and photorealism. "
    "Be technical, concise, and constructive. "
    "If asked to generate an image, you CAN do it (if provided tool allows). "
    "ALWAYS respect the requested Aspect Ratio and Resolution style in the prompt."
)
