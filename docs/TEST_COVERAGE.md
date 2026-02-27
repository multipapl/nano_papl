# 🧪 Test Coverage Overview

**Last Updated**: 2026-01-18  
**Total Tests**: 83  
**Status**: ✅ All Passing

---

## 1. Coverage Summary

| Category | Tests | Coverage | Status |
|----------|-------|----------|--------|
| **Core Logic** | 35 | ~85% | ✅ Excellent |
| **Business Services** | 10 | ~75% | ✅ Good |
| **UI Pages** | 38 | ~65% | ✅ Solid |

---

## 2. Core Logic & Utilities

| Component | Test File | Tests | Description |
| :--- | :--- | :--- | :--- |
| **Base Worker** | `test_base_worker.py` | 3 | Signal flow, error handling, graceful stop |
| **Chat Worker** | `test_chat_worker.py` | 2 | GenerationResult emission, timing |
| **Prompt Generator** | `test_generator.py` | 3 | Markdown generation, season logic, Xmas variants |
| **History Manager** | `test_history_manager.py` | 4 | Session CRUD, folder management |
| **Config Helper** | `test_config_helper.py` | 3 | JSON I/O, Keyring security, ConfigManager |
| **Constants** | `test_constants.py` | 3 | Resolution linearity, aspect ratios |
| **Error Manager** | `test_error_manager.py` | 6 | Singleton, reporting, history limits |
| **Resource Manager** | `test_resource_manager.py` | 8 | Singleton, path resolution, properties |
| **LLM Client** | `test_llm_client.py` | 3 | Provider factory, chat abstraction |

---

## 3. Business Services

| Component | Test File | Tests | Description |
| :--- | :--- | :--- | :--- |
| **Comfy Orchestrator** | `test_comfy_orchestrator.py` | 2 | Batch scanning, multi-node workflows |
| **Generation Service** | `test_generation_service.py` | 3 | Gemini API flow, filename verification |
| **Image Resizer** | `test_image_resizer_service.py` | 5 | Proportional scaling, Lanczos resampling |

---

## 4. UI Components

| Component | Test File | Tests | Description |
| :--- | :--- | :--- | :--- |
| **Constructor Page** | `test_constructor_page.py` | 7 | Init, widgets, state save/load, navigation |
| **Tools Page** | `test_tools_page.py` | 4 | Init, ValidatorWidget, ResizerWidget |
| **Batch Page** | `test_batch_page.py` | 7 | Init, ConfigPanel, MonitorPanel, worker |
| **Chat Page** | `test_chat_page.py` | 4 | Message flow, sidebar, interface init |
| **Settings Page** | `test_settings_page.py` | 2 | API key preservation |
| **Navigation** | `test_navigation.py` | 1 | Window init, page switching |
| **Theme System** | `test_theme.py` | 3 | Theme switching, ThemeAwareBackground |
| **Components** | `test_components.py` | 2 | NPButton, message bubbles |
| **Sidebar** | `test_sidebar.py` | 3 | Init, populate, signals |
| **Other UI** | Various | 5 | Drag-drop, error handling, live config |

---

## 5. How to Run

```powershell
# Full Suite with Coverage
python run_tests.py

# Core Only
pytest tests/core

# UI Only  
pytest tests/ui

# With Coverage Report
pytest --cov=core --cov=ui --cov-report=html
```

> [!TIP]
> Coverage HTML report will be in `htmlcov/index.html`.
