# Changelog

All notable changes to this project will be documented in this file.

## [2.1.0] - 2026-02-27
### Added
- **API Usage Statistics** (`settings_page.py`, `config_helper.py`):
  - Monthly generation counter (consolidated chat + batch into single metric)
  - Daily RPD (Requests Per Day) tracker migrated from Batch page to Settings
  - Month selector dropdown to view historical statistics
  - Auto-refresh when opening Settings tab (`showEvent` override)
  - "Clear Data" button to reset all local statistics
  - Statistics block moved to the top of the Settings page

- **Estimated API Cost Tracking** (`constants.py`, `config_helper.py`, `settings_page.py`):
  - Resolution-based pricing: 1K/2K = $0.14, 4K = $0.24 per generation
  - Cost displayed as `$X.XX` in Settings alongside generation count
  - Text-only chat responses are excluded from tracking (free)

- **Chat Stop Button** (`input_area.py`, `control_panel.py`, `chat_page.py`):
  - Red ✕ button in chat toolbar to force-stop active generation
  - Kills worker thread, hides typing indicator, re-enables input

### Fixed
- **Chat UI Lock on Session Switch** (`chat_page.py`): Switching chats during generation no longer permanently locks the input. `on_response` and `on_error` now use `try/finally` to guarantee UI re-enabling.
- **Chat Worker Crash on Text Responses** (`chat_worker.py`): Fixed `NameError` where `response_image_path` was uninitialized when the AI returned text-only, silently killing the worker thread.
- **Incorrect Cost Tracking** (`chat_worker.py`): Chat now passes the actual selected resolution tier (1K/2K/4K) instead of a hardcoded default.

### Changed
- RPD counter and related UI removed from `batch_page.py` and `config_panel.py` (centralized in Settings)
- `track_api_usage()` parameter changed from `source` to `resolution_tier` for cost calculation

---

## [2.0.0rc] - 2026-01-18
### Added
- **Modern UI (Complete Rewrite)**:
  - Migrated to QFluentWidgets for native Fluent Design experience
  - Modular chat interface with `ChatSidebar`, `ChatMessageDisplay`, `ChatControlPanel`
  - Theme-aware components with automatic dark/light mode switching
  - Drag & drop chat sessions between folders
  - Modern composite input area (Claude/Cursor-style)
  - Settings page with live configuration persistence

- **Batch Processing Enhancements**:
  - "Save individual .txt logs" checkbox option
  - Default resolution set to 2K
  - Log saving preference passed to workers

- **Documentation**:
  - `docs/INDEX.md` — documentation reference index
  - `docs/ARCHITECTURE.md` — high-level system design
  - `docs/FUTURE_PLAN.md` — backlog tracking with status system

### Changed
- **Project Structure**: Reorganized UI into `ui/pages/` and `ui/widgets/` hierarchy
- **Configuration**: Centralized constants in `core/constants.py`
- **Theme System**: All colors now use `UIConfig` + `ThemeAwareBackground`

### Fixed
- **Chat Deletion Bug**: Fixed infinite "New Chat" loop when deleting chats
- **Settings Import**: Resolved `NameError` with missing `QHBoxLayout` import
- **Button Focus State**: Fixed visual glitch with dropdown buttons remaining "pressed"
- **Image Attachment**: Fixed right-click attachment from chat history

---

## [1.3.0] - 2026-01-10
### Added
- **Batch Generator Improvements**:
  - Added option to select output image format (JPG/PNG).
  - Integrated Daily API Call Counter (RDP Counter) to track usage.
  - Implemented filename cleanup logic (removed `_+_` and ` + ` patterns).
- **Constructor UI Overhaul**:
  - Implemented hierarchical view for seasons and lighting.
  - Added a new component-based presets system.

### Changed
- **Core Refactoring**: Major codebase reorganization to improve modularity and maintainability.
- **Configuration**: Updated `.gitignore` to include `run.bat` and clean up tracked temporary files.

### Fixed
- **DaVinci Resolve Compatibility**: Fixed PNG saving issue to ensure generated images are correctly recognized by DaVinci Resolve.

## [1.2.1] - 2026-01-05
### Added
- New Git workflow: multi-branch strategy with `dev` (working branch) and `main` (clean releases).
- Comprehensive Git workflow guide ([docs/git_workflow.md](docs/git_workflow.md)).
- Project `CHANGELOG.md` to track version history.

### Changed
- Standardized executable naming in `dist/` folder (format: `NanoPapl_vX.X.X.exe`).
- Updated `.gitignore`: `docs/` folder is now ignored on GitHub but kept locally.

---

## [1.2.0] - 2026-01-05
### Added
- **Batch Generation ETA**: The application now displays the estimated time of arrival for batch processing.
- **Resolution Validation**: Automatic marking of generated images with the `_diff` suffix if their resolution differs from the input.

### Fixed
- **Progress Bar**: Fixed the display bug during batch generation.
- **Subfolder Optimization**: Improved subproject folder handling (creating the `optimized` directory within the project and utilizing its contents correctly).
