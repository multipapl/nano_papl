# 🛠️ Nano Papl Development Guide

This guide defines the standards and procedures for extending and maintaining Nano Papl.

---

## 1. UI Development Principles

We use **Fluent Design** via the `qfluentwidgets` library. Follow these rules to ensure visual consistency.

### A. Modular Widgets
Never build complex layouts directly in a Page. Instead, create a widget in `ui/widgets/`.
1. **Inherit**: Use `QWidget` or `QFrame`.
2. **Styling**: Use `ThemeAwareBackground` for containers.
3. **Signals**: Expose internal events via `Signal`.
   - *Example*: `sendClicked = Signal(str)`

### B. Dependency Injection
Managers (like `HistoryManager`) must be passed into the constructor, never initialized inside it.
```python
def __init__(self, history_manager: HistoryManager, parent=None):
    super().__init__(parent)
    self.history_manager = history_manager
```

### C. Native Theming
- **No hardcoded CSS**: Avoid `setStyleSheet("background: #272727")`.
- **Theme Connection**: Connect to `qconfig.themeChanged` to update custom colors.
- **Components**: Use `ui.components` primitives (e.g., `NPButton`, `SectionCard`).

---

## 2. Adding a New Page

1.  **Create Orchestrator**: Add a new file in `ui/pages/` (e.g., `analytics_page.py`).
2.  **Modularize**: Break the UI into widgets in `ui/widgets/analytics/`.
3.  **Register**: Add the page to `ModernWindow` in `ui/window.py`:
    ```python
    self.analytics_interface = AnalyticsPage(self)
    self.addSubInterface(self.analytics_interface, FluentIcon.BASKETBALL, "Analytics")
    ```

---

## 3. Asynchronicity (Workers)

The UI thread must **never block**. All API calls or heavy processing must use `QThread`.
1.  **Worker**: Inherit from `QThread` in `core/workers/`.
2.  **Signals**: Define signals for data return (e.g., `result_received`).
3.  **Management**: Ensure `deleteLater()` is called on finish to avoid memory leaks.

---

## 4. Best Practices Summary (The "LEGO" Rule)

- widgets are **bricks** (UI + Small State).
- pages are **instructions** (Orchestrating bricks).
- services are **material** (Business logic).

For deep-dive UI patterns, refer to [QFluentWidgets Survival Guide](file:///q:/Blender_Python/Nano_Papl/docs/QFLUENTWIDGETS_GUIDE.md).
