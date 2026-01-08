# Development Guides

## 1. How to Add a New Field (UI)
To add a setting or input that persists automatically:

1.  **Instantiate Widget**: Create your widget (e.g., `QLineEdit`, `QCheckBox`, or custom widget).
2.  **Register Field**: In your Tab's `_register_fields()` method (or `__init__`):
    ```python
    self.my_input = QLineEdit()
    # "user_name" will be the key in config.json
    self.register_field("user_name", self.my_input)
    ```
3.  **Custom Widgets**: If using a custom widget, implement:
    *   `get_state() -> Any`
    *   `set_state(value: Any)`
    *   `modified = Signal()` (optional, for auto-save)

## 2. How to Add a New Service
1.  **Create Service**: Add a new file in `core/services/` (e.g., `analytics_service.py`).
    ```python
    class AnalyticsService:
        def track_event(self, event_name):
            ...
    ```
2.  **Injection**: Initialize it in `main.py` or within the specific Tab that needs it.
    ```python
    # Inside a Tab
    self.analytics = AnalyticsService()
    ```
3.  **Usage**: Call service methods from UI handlers or Workers.

## 3. How to Add a Test
We use `pytest`.

1.  **Location**: Create a new file in `tests/` matching the pattern `test_*.py`.
2.  **Structure**:
    ```python
    from core.services.my_service import MyService

    def test_service_logic():
        service = MyService()
        result = service.calculate(10)
        assert result == 100
    ```
3.  **Run Tests**:
    *   Terminal: `pytest`
    *   Or run `run_tests.py` in root.
