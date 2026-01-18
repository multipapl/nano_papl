# 🛠️ Nano Papl Development Guide

This guide defines the standards and procedures for extending and maintaining Nano Papl.

---

## 1. UI Development Principles

We use **Fluent Design** via the `qfluentwidgets` library.

### A. Page Structure (NPBasePage)
All pages must inherit from `NPBasePage` (`ui/components.py`):
```python
from ui.components import NPBasePage

class MyPage(NPBasePage):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._setup_ui()
```
**Benefits:**
- Pre-configured `main_layout` with zero margins.
- Built-in `showStateToolTip()` / `finishStateToolTip()` for progress feedback.
- `addScrollArea(widget)` helper for scrollable content.

### B. Dependency Injection
Managers must be passed into constructors, never initialized inside:
```python
def __init__(self, config_manager, parent=None):
    super().__init__(parent)
    self.config_manager = config_manager  # ConfigManager instance
```

### C. Configuration Access
Use the object-oriented `ConfigManager` pattern:
```python
# ✅ Correct (type-safe, auto-completable)
api_key = self.config_manager.config.api_key
theme = self.config_manager.config.theme_color

# After modifying:
self.config_manager.config.theme_color = "#ff0000"
self.config_manager.save()
```

### D. Native Theming
- **Design Tokens**: Use `UIConfig` for all colors.
- **Theme Connection**: Inherit from `ThemeAwareBackground` for containers.
- **Shared Components**: Use `NPButton`, `SectionCard`, etc.

---

## 2. Adding a New Page

1.  **Create Orchestrator**: Add file in `ui/pages/` (e.g., `analytics_page.py`).
2.  **Inherit NPBasePage**: Pass `config_manager` to constructor.
3.  **Register in Window**:
    ```python
    # ui/window.py
    self.analytics_interface = AnalyticsPage(self.config_manager, self)
    self.addSubInterface(self.analytics_interface, FluentIcon.BASKETBALL, "Analytics")
    ```

---

## 3. Asynchronicity (Workers)

The UI thread must **never block**. All workers must inherit from `BaseWorker`:

```python
from core.workers.base_worker import BaseWorker

class MyWorker(BaseWorker):
    custom_signal = Signal(str)
    
    def execute(self):
        # Heavy work here...
        self.custom_signal.emit("result")
```

**BaseWorker guarantees:**
- `finished_signal` always emitted (even on exception).
- `is_running` flag for safe stopping.
- `response_signal` and `error_signal` pre-defined.

---

## 4. Progress Feedback

For long-running operations, use `StateToolTip` via `NPBasePage`:

```python
# In your page (inheriting NPBasePage)
def start_generation(self):
    self.showStateToolTip("Generating...", "Please wait")
    self.worker.start()

def on_worker_finished(self, result):
    self.finishStateToolTip("Complete!", success=True)
```

---

## 5. Security Best Practices

- **Never save API keys to JSON**: Use `keyring` via `ConfigManager`.
- **Use ConfigManager**: `self.config_manager.config.api_key` handles caching.
- **Validate in UI**: Check key format before saving.

---

## 6. Error Handling (`ErrorManager`)

All errors should be reported through the centralized `ErrorManager`:

```python
# In any page (inheriting NPBasePage)
self.showError("Failed to connect to API", context="ChatPage")

# Or directly via singleton
from core.utils.error_manager import error_manager, ErrorSeverity

error_manager.report(
    "Connection timeout",
    severity=ErrorSeverity.WARNING,
    context="BatchWorker",
    details=traceback.format_exc()
)
```

**Severity Levels:**
- `INFO`: Silent logging only.
- `WARNING`: Yellow InfoBar notification.
- `ERROR`: Red InfoBar notification (default).
- `CRITICAL`: Red InfoBar + logged with full details.

### Logging
All application logs are automatically:
- **Rotated** at 5MB with 5 backup files retained
- **Stored** in `AppData/Roaming/NanoPapl/logs/`
- **Named** as `nanopapl_YYYY-MM-DD.log`

Use the global logger:
```python
from core.logger import logger

logger.info("Operation started")
logger.error("Something failed", exc_info=True)
```

---

## 7. Testing Standards

### Execution
```powershell
.\.venv\Scripts\python.exe scripts\run_tests.py
```

### Key Points
- **Path Isolation**: Use `tmp_path` fixture for all file operations.
- **ConfigManager Reset**: Call `config_manager.reload()` after patching paths.
- **Signal Testing**: Use `qtbot.waitSignal()` for async verification.

---

## 8. Git Workflow (Solo Developer)

### Daily Development (Branch `dev`)
Use the `dev` branch for all active work:
```bash
git checkout dev
git add .
git commit -m "feat: added new message grouping logic"
```

### Release Procedure
When a version is ready (e.g., `v2.0.0`):
1. **Version Bump**: Update `APP_VERSION` in `core/constants.py`.
2. **Build**: `python scripts/build.py`
3. **Merge to Main** (Squash):
```bash
git checkout main
git merge --squash dev
git commit -m "Release v2.0.0: Description"
git tag v2.0.0
git push origin main --tags
```

### Commit Message Standard
- `feat:`: New feature
- `fix:`: Bug fix
- `refactor:`: Code change (no new feature/fix)
- `docs:`: Documentation
- `perf:`: Performance

---

## 9. QFluentWidgets Guide

### Core Philosophy
QFluentWidgets — "golden cage": gives top Windows 11 style out of the box, but requires following rules.

### ✅ Native Theming (CRITICAL!)
Use `paintEvent` + `QPainter` instead of `setStyleSheet`:
```python
from qfluentwidgets import isDarkTheme, qconfig

class ThemeAwareBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.light_bg = QColor("#ffffff")
        self.dark_bg = QColor("#272727")
        qconfig.themeChanged.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.dark_bg if isDarkTheme() else self.light_bg)
        painter.drawRect(self.rect())
```

### 🚫 Never Do This
```python
# ❌ Hardcoded colors without theme reaction
widget.setStyleSheet("background: #ffffff;")

# ❌ Fixed pixel sizes
widget.setFixedSize(300, 200)

# ❌ Heavy logic in UI thread
data = requests.get(url).json()

# ❌ setStyleSheet on Fluent widgets
PrimaryPushButton.setStyleSheet("background: red;")
```

### High DPI
```python
# ❌ NOT THIS
widget.setFixedSize(300, 200)

# ✅ THIS
widget.setMinimumSize(300, 200)
widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

# For fonts - use pt, not px
font.setPointSize(10)  # Auto-scales
```

### InfoBar for Notifications
```python
from qfluentwidgets import InfoBar, InfoBarPosition

InfoBar.success(
    title="Success",
    content="Operation completed",
    parent=self,
    duration=2000,
    position=InfoBarPosition.TOP
)
```

### Quick Reference

| Component | Usage |
|-----------|-------|
| `CardWidget` | Base container with shadow |
| `SimpleCardWidget` | Simplified card |
| `SettingCardGroup` | Settings group |
| `InfoBar` | Notifications |
| `StateToolTip` | Progress indicator |
| `FluentWindow` | Main window with navigation |

### Useful Utilities
```python
from qfluentwidgets import (
    isDarkTheme,      # Check theme
    themeColor,       # Accent color
    setTheme,         # Change theme
    qconfig,          # Global config
    Theme             # Enum: LIGHT, DARK, AUTO
)
```

---

## 10. Best Practices Summary

- Pages are **orchestrators** (inherit `NPBasePage`).
- Widgets are **bricks** (self-contained UI + local state).
- Workers are **executors** (inherit `BaseWorker`).
- Config is **centralized** (use `ConfigManager`).
- Errors are **reported** (use `ErrorManager`).
- Use **Fluent components** — don't fight the library.
