# 🏗️ Nano Papl Architecture

This document provides a high-level overview of the application's architecture, focused on the **Modern UI (v2)** and its modular component-based system.

## 1. Project Overview

Nano Papl is built on a **Modular Component Architecture**. Instead of monolithic tabs, every interface is composed of specialized widgets that communicate via signals.

### Directory Structure

```text
Nano_Papl/
├── main.py                     # Entry point (ModernWindow)
├── data/
│   ├── templates.json          # Prompt templates & lighting definitions
│   └── api_nano_banana_pro.json # Generation workflow definitions
├── core/
│   ├── services/               # Stateless business logic
│   │   ├── comfy_orchestrator.py
│   │   ├── generation_service.py
│   │   └── image_resizer_service.py
│   ├── workers/                # QThread wrappers for async tasks
│   │   ├── chat_worker.py
│   │   ├── batch_worker.py
│   │   └── comfy_worker.py
│   ├── utils/
│   │   ├── config_helper.py    # Per-user settings persistence
│   │   └── resource_helper.py
│   └── history_manager.py      # Chat session persistence
└── ui/
    ├── window.py               # Main FluentWindow (Shell)
    ├── components.py           # Shared UI primitives (Buttons, Cards, Labels)
    ├── pages/                  # Tab Orchestrators (Chat, Batch, etc.)
    └── widgets/                # specialized components (Sidebar, InputArea, etc.)
```

## 2. Core Patterns

### 🧩 Component-Based UI
Every page (e.g., `ChatInterface`) is just a container that orchestrates multiple sub-widgets (e.g., `ChatSidebar`, `ChatInputArea`).
- **Isolation**: Widgets handle their own internal styling and state.
- **Communication**: Widgets use **Qt Signals** to talk to the parent page.
- **Independence**: Widgets should not know about the managers directly.

### 💉 Dependency Injection
The `ModernWindow` (in `ui/window.py`) initializes shared managers (`HistoryManager`, `Config`) and "injects" them into the pages during instantiation. This ensures a single source of truth and easier testing.

### 🧵 Async Execution (Workers)
Never run heavy logic (API calls, file I/O) in the main UI thread. 
- Use classes from `core/workers/`.
- Connect signals (`response_signal`, `progress_signal`) to UI update slots.

## 3. Data Persistence

| Data Type | Storage | Manager |
| :--- | :--- | :--- |
| **User Settings** | `config.json` (AppData) | `config_helper.py` |
| **User Presets** | `presets.json` (AppData) | `config_helper.py` |
| **Chat History** | `.json` files (Documents) | `history_manager.py` |
| **Temp Files** | `temp/` folder (Root) | `PathProvider` |

## 4. Key Dependencies

- **PySide6**: Core framework.
- **QFluentWidgets**: Modern UI design system (Fluent Design).
- **Google GenAI**: Gemini API integration.
- **Pillow**: Image optimization and previews.
