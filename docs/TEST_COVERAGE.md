# 🧪 Test Coverage Overview

This document details the current test coverage for Nano Papl v2, providing a map of verified components and their testing methodology.

## 1. Core Logic & Utilities

| Component | Test File | Coverage Description |
| :--- | :--- | :--- |
| **Prompt Generator** | `tests/core/test_generator.py` | Markdown generation, season logic, and Xmas variants. |
| **History Manager** | `tests/core/test_history_manager.py` | Session creation, folder management, and disk persistence. |
| **Config Helper** | `tests/core/test_config_helper.py` | JSON configuration loading/saving and Keyring security. |
| **Constants** | `tests/core/test_constants.py` | Resolution table linearity, aspect ratio accuracy, and AI compatibility. |
| **LLM Client** | `tests/core/test_llm_client.py` | Provider factory selection and chat generation abstraction. |

## 2. Business Services

| Component | Test File | Coverage Description |
| :--- | :--- | :--- |
| **Comfy Orchestrator** | `tests/core/test_comfy_orchestrator.py` | Batch scanning, multi-node workflow updates, and the upload-queue-history-download cycle. |
| **Generation Service** | `tests/core/test_generation_service.py` | Gemini API communication flow and filename/resolution verification during save. |
| **Image Resizer** | `tests/core/test_image_resizer_service.py` | Proportional scaling math, Lanczos resampling call, and recursive folder scanning. |

## 3. UI & User Interface

| Component | Test File | Coverage Description |
| :--- | :--- | :--- |
| **Navigation** | `tests/ui/test_navigation.py` | Main window initialization and page switching. |
| **Theme System** | `tests/ui/test_theme.py` | dynamic theme switching, `ThemeAwareBackground` responsiveness, and bubble color sync. |
| **Chat Page** | `tests/ui/test_chat_page.py` | Message sending flow, sidebar toggling, and interface initialization. |
| **Settings Page** | `tests/ui/test_settings_page.py` | API key preservation and general settings interaction. |
| **Components** | `tests/ui/test_components.py` | `NPButton` behavior, message bubble styling, and auto-expanding text edits. |
| **Drag & Drop** | `tests/ui/test_drag_drop.py` | Files/folder drop overlay visibility logic. |

## 4. How to Run

1. **Full Suite**: `python run_tests.py`
2. **Core Only**: `pytest tests/core`
3. **UI Only**: `pytest tests/ui`

> [!TIP]
> Use `pytest -s` to see log output and print statements during development.
