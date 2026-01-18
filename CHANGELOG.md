# Changelog

All notable changes to this project will be documented in this file.

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
