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
- **Design Tokens**: Use `ui.components:UIConfig` for all colors and dimensions.
  - *Example*: `self.setStyleSheet(f"background: {UIConfig.CARD_BG_DARK}")`
- **Theme Connection**: Containers should inherit from `ThemeAwareBackground`.
- **Shared Components**: Use `ui.components` primitives (e.g., `NPButton`, `SectionCard`).

### D. Common UI Patterns
- **Hybrid Input (ComboBox + LineEdit)**: Used in constructors. The ComboBox provides templates, while the LineEdit allows manual overrides. 
  - *Best Practice*: Selecting a template should auto-fill the LineEdit to allow immediate further customization.
- **Visibility Management**: Use `QWidget.show()/hide()` in parent orchestrators to adapt the global toolbar based on the active sub-tab (e.g., hiding bulk generation buttons during single prompt assembly).

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

---

## 4. Security Best Practices

Nano Papl enforces a strict **separation between sensitive data and configuration logic**.

### Managing API Keys
1. **Never Save to Files**: Do NOT hardcode or write API keys into `config.json` or any local file.
2. **Use Keyring**: Always use `keyring.set_password` and `keyring.get_password`.
3. **Use the Helper**: Prefer `config_helper.get_value("api_key")` which handles the memory cache automatically.
4. **Validation**: Validate key format/length in the UI before passing it to the core layer.

---

## 5. Image & Hardware Protocols

Consistency in image IO is critical for application stability on different hardware.

### A. Image Storage
Always use `core.utils.image_utils` for saving or modifying images:
- **`save_image_with_format`**: Automatically handles format conversion (e.g., stripping Alpha channel for JPG) and creates directories as needed.
- **`get_or_create_thumbnail`**: Use this for UI previews to minimize RAM usage.

### B. Shared Logic
When adding a new generation feature, reuse `ui.components:GenerationConfigWidget`. This ensures that user selections for resolution and aspect ratios are handled identically across the whole app.

---

## 6. Testing Standards

We maintain two test suites in the `tests/` directory.

### A. Execution
Always use the root test runner to ensure environment parity:
```powershell
python run_tests.py
```

### B. Methodology
- **Mocks**: When testing services, mock the `genai.Client` and `ComfyAPI` to avoid external dependencies.
- **Path Isolation**: Use `pytest` fixture `tmp_path` for all file operations.
- **Verification**: UI tests must verify both state changes and theme-adaptive styling.

---

## 7. Best Practices Summary (The "LEGO" Rule)

- widgets are **bricks** (UI + Small State).
- pages are **instructions** (Orchestrating bricks).
- services are **material** (Business logic).

For deep-dive UI patterns, refer to [QFluentWidgets Survival Guide](file:///q:/Blender_Python/Nano_Papl/docs/QFLUENTWIDGETS_GUIDE.md).
