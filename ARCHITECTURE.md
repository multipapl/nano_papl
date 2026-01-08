# Architecture Passport

## Project Structure
```
Nano_Papl/
├── core/                   # Business logic and backend services
│   ├── services/           # Stateful services (GenAI, Automation)
│   ├── workers/            # QThread workers for async tasks
│   ├── factories/          # Factory patterns (LLM, UI)
│   ├── utils/              # Stateless helpers (Paths, Config, Images)
│   └── managers/           # Logic managers (History, Comfy)
├── ui/                     # User Interface (PySide6)
│   ├── widgets/            # Reusable UI components
│   └── tab_*.py            # Main application tabs
├── tests/                  # Test suite (pytest)
├── assets/                 # Icons and static resources
├── data/                   # JSON storage (presets, history)
└── main.py                 # Application entry point
```

## UI Architecture (BaseTab)
The UI is built on `BaseTab`, a custom `QWidget` that provides automated state management.

### Key Logic:
1.  **Registry System**: Widgets are registered with `self.register_field("key", widget)`.
2.  **Auto-State**:
    *   `save_state()`: Iterates registry, extracts values via `.get_state()` or standard PySide getters, and saves to `config.json`.
    *   `load_state()`: Hydrates widgets from `config.json` on startup.
3.  **Observers**: Widgets implementing the `modified` signal triggers auto-save (debounced).

## Service Layer (Core)
The Core layer is decoupled from UI, communicating via Signals or direct Service injection.

### key Components:
*   **GenerationService**: Handles AI image generation (Google GenAI), image processing, and file I/O.
*   **ComfyOrchestrator**: Manages ComfyUI processes (Start/Stop) and API interactions.
*   **BatchWorker**: Background thread for processing queues. Uses `GenerationService` internally.
*   **PathProvider**: Central source of truth for all filesystem paths, ensuring cross-platform compatibility.
