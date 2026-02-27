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

## 8. Git Workflow & Versioning

### Branch Strategy

```
main ────●────────●────────●───── (stable releases only, tagged)
          \      / \      /
dev ───●───●────●───●────●──────  (daily work, all commits)
```

| Branch | Purpose | When to Push |
|--------|---------|--------------|
| `dev` | Active development | Every commit |
| `main` | Stable releases only | Only on release |

### Semantic Versioning (SemVer)

```
MAJOR.MINOR.PATCH[-prerelease]

Examples:
  2.0.0rc    → Release Candidate (testing phase)
  2.0.0      → Stable release
  2.0.1      → Patch (bug fixes only)
  2.1.0      → Minor (new features, backward compatible)
  3.0.0      → Major (breaking changes)
```

**Version is stored in:** `core/constants.py` → `APP_VERSION`

### Daily Development Flow

```bash
# Always work in dev
git checkout dev

# Make changes, commit often
git add -A
git commit -m "fix: resolved chat deletion loop bug"

# Push to remote
git push origin dev
```

### Release Procedure

**1. Prepare Release (in dev):**
```bash
# Update version in core/constants.py
APP_VERSION = "2.0.0"  # Remove -dev or rc suffix

# Update CHANGELOG.md with release notes

# Commit the version bump
git add -A
git commit -m "chore: bump version to 2.0.0"
```

**2. Build & Test:**
```bash
python scripts/build.py
# Test the EXE thoroughly!
```

**3. Merge to Main:**
```bash
git checkout main
git merge dev
git push origin main
```

**4. Tag the Release:**
```bash
git tag v2.0.0
git push origin --tags
```

**5. Start New Development Cycle:**
```bash
git checkout dev
# Immediately bump to next dev version
APP_VERSION = "2.0.1-dev"  # or "2.1.0-dev" for features
git add -A
git commit -m "chore: start 2.0.1-dev cycle"
git push origin dev
```

### Hotfix Procedure (Critical Bug in Production)

```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug

# Fix the bug, bump patch version
APP_VERSION = "2.0.1"

# Merge back to main
git checkout main
git merge hotfix/critical-bug
git tag v2.0.1
git push origin main --tags

# Also merge to dev
git checkout dev
git merge hotfix/critical-bug
git push origin dev

# Cleanup
git branch -d hotfix/critical-bug
```

### Commit Message Standard

| Prefix | Usage |
|--------|-------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `refactor:` | Code restructure (no behavior change) |
| `docs:` | Documentation only |
| `chore:` | Build, tooling, version bumps |
| `perf:` | Performance improvement |
| `test:` | Adding/fixing tests |

**Examples:**
```
feat: add folder drag-and-drop in chat sidebar
fix: resolve infinite loop in chat deletion
refactor: extract message display into separate widget
docs: update Git workflow section
chore: bump version to 2.0.0
```

### Version Lifecycle Example

```
v2.0.0rc   → Testing with users
v2.0.0     → Stable release (tag, merge to main)
v2.0.1-dev → Start new cycle immediately
v2.0.1     → Patch with bug fixes
v2.1.0-dev → Start feature cycle
v2.1.0     → Minor release with new features
```

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
