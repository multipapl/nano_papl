# 🏗️ Nano Papl Architecture

This document provides a high-level overview of the application's architecture.

## 1. Project Overview

Nano Papl is built on a **Modular Component Architecture**. Every interface is composed of specialized widgets that communicate via signals.

### Directory Structure

```text
Nano_Papl/
├── main.py                     # Entry point (ModernWindow)
├── data/
│   ├── templates.json          # Prompt templates & lighting definitions
│   └── api_nano_banana_pro.json # Generation workflow definitions
├── core/
│   ├── models.py               # Shared data models (AppConfig, GenerationResult)
│   ├── services/               # Stateless business logic
│   │   ├── comfy_orchestrator.py
│   │   ├── generation_service.py
│   │   └── image_resizer_service.py
│   ├── workers/                # QThread wrappers for async tasks
│   │   ├── base_worker.py      # ⬅️ NEW: Unified base class for all workers
│   │   ├── chat_worker.py
│   │   ├── batch_worker.py
│   │   └── comfy_worker.py
│   ├── utils/                  # Shared utilities
│   │   ├── config_helper.py    # ⬅️ ConfigManager singleton for settings
│   │   └── path_provider.py
│   └── history_manager.py      # Chat session persistence
├── ui/
│   ├── window.py               # Main FluentWindow (Shell)
│   ├── components.py           # UIConfig tokens, NPBasePage, shared primitives
│   ├── pages/                  # Tab Orchestrators (all inherit from NPBasePage)
│   └── widgets/                # Specialized sub-components
└── tests/                      # Unified Test Suite
```

## 2. Core Patterns

### 🧩 Component-Based UI
Every page (e.g., `ChatInterface`) is just a container orchestrating sub-widgets.
- **Base Class**: All pages inherit from `NPBasePage` for consistent layout and theming.
- **Isolation**: Widgets handle their own styling and state.
- **Communication**: Widgets use **Qt Signals** to talk to parents.

### 💉 Dependency Injection
`ModernWindow` initializes shared managers and injects them into pages:
```python
# ModernWindow.__init__
self.config_manager = config_helper.config_manager  # Singleton
self.chat_interface = ChatInterface(history_manager, self.config_manager, self)
```

### 🗂️ Object-Oriented Configuration (`ConfigManager`)
All application settings are managed via a centralized `ConfigManager` singleton:
- **Model**: `AppConfig` dataclass in `core/models.py` provides typed access.
- **Secure Storage**: API keys are stored in the system keyring (Windows Credential Manager).
- **Persistence**: Non-sensitive settings saved to `AppData/Roaming/NanoPapl/config.json`.

```python
# Old way (deprecated)
api_key = config_helper.get_value("api_key")

# New way (type-safe)
api_key = self.config_manager.config.api_key
```

### ⚡ Async Execution (`BaseWorker`)
All workers inherit from `BaseWorker` in `core/workers/base_worker.py`:
- **Guaranteed Signals**: `finished_signal` always emitted (even on error).
- **Lifecycle**: `start()` → `execute()` → `finished_signal.emit()`.
- **Stopping**: `stop()` sets `is_running = False`.

```python
class ChatWorker(BaseWorker):
    def execute(self):
        # Heavy work here...
        self.response_signal.emit(result)
```

### 📣 Progress Feedback (`StateToolTip`)
Long-running operations use `StateToolTip` for non-blocking user feedback:
```python
self.showStateToolTip("Generating...", "Please wait")  # NPBasePage method
# ... later ...
self.finishStateToolTip("Done!", success=True)
```

### 📦 Standardized Worker Outputs (`GenerationResult`)
All workers emit a unified `GenerationResult` object for consistent handling:
```python
from core.models import GenerationResult

# Success with text and optional image
result = GenerationResult.ok(
    text="Response from AI",
    image_path="/path/to/image.png",
    session_id="abc123",
    model_id="gemini-3-pro",
    execution_time_ms=1500
)

# Error case
result = GenerationResult.error("API connection failed")

# UI handler unpacks the result
def on_response(self, result):
    if result.success:
        self.display_message(result.text_response)
    else:
        self.show_error(result.error_message)
```

## 3. Data Storage

| Data Type | Storage Location | Manager |
| :--- | :--- | :--- |
| **API Keys** | System Keyring + RAM Cache | `ConfigManager` |
| **User Settings** | `AppData/NanoPapl/config.json` | `ConfigManager` |
| **User Presets** | `AppData/NanoPapl/presets.json` | `config_helper.PRESETS_FILE` |
| **Chat History** | `Documents/NanoPapl/sessions/` | `HistoryManager` |
| **Application Logs** | `AppData/NanoPapl/logs/` | `Logger` (rotating, 5MB × 5 files) |

### 🚨 Centralized Error Handling (`ErrorManager`)
All errors are reported through a central `ErrorManager` singleton:
```python
from core.utils.error_manager import error_manager, ErrorSeverity

# Report an error (auto-logged and shown in UI)
error_manager.report("Connection failed", severity=ErrorSeverity.ERROR, context="ChatWorker")

# Or via NPBasePage helper
self.showError("API key invalid", context="SettingsPage")
```

| **API Keys** | System Keyring + RAM Cache | `ConfigManager` |
| **User Settings** | `AppData/NanoPapl/config.json` | `ConfigManager` |
| **User Presets** | `AppData/NanoPapl/presets.json` | `config_helper.PRESETS_FILE` |
| **Chat History** | `Documents/NanoPapl/sessions/` | `HistoryManager` |
| **Application Logs** | `AppData/NanoPapl/logs/` | `Logger` |

## 4. Security

- **Zero-Plaintext**: API keys never written to JSON files.
- **Keyring Backend**: OS-level secure vault.
- **RAM Caching**: Keys cached after first retrieval for performance.

## 5. Key Dependencies

- **PySide6**: Core framework.
- **QFluentWidgets**: Modern Fluent Design UI.
- **Google GenAI**: Gemini API integration.
- **Pillow**: Image processing.
- **Keyring**: Cross-platform secure storage.

### 📂 Centralized Resource Access (`ResourceManager`)
All asset paths are managed through a central `ResourceManager` singleton:
```python
from core.utils.resource_manager import Resources

# Get data files
templates = Resources.get_data_file("templates.json")

# Get icons with caching and fallback
icon = Resources.icon("send")  # Returns QIcon

# Check if resource exists
if Resources.exists("assets/custom_icon.png"):
    ...
```

## 6. AI Models

| Model ID | Use Case |
|----------|----------|
| `gemini-3-pro-image-preview` | High-quality image generation (multimodal) |
| `gemini-3-flash-preview` | Fast text-based analysis |
