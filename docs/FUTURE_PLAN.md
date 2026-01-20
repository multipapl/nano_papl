# 🔮 Future Development Plan

This document outlines planned architectural improvements for Nano Papl.

> [!IMPORTANT]
> **Document Rules:**
> - **Never delete entries** — only update their status when resolved
> - Move completed items to the `📜 Completed` section at the bottom
> - Add completion date and version (e.g., `Resolved: v1.3.1, 2026-01-18`)
> - This file serves as the **single source of truth** for all tasks, bugs, and improvements

**Status Legend:**
| Status | Meaning |
|--------|---------|
| 🔴 To Fix | High priority bug, blocking |
| 🟡 Planned | Approved for implementation |
| 🔵 In Progress | Currently being worked on |
| ⚪ Backlog | Low priority, future consideration |
| 🟢 Completed | Done, moved to Completed section |



## Plugin Architecture for Tools

**Status:** Planned  
**Priority:** Medium (when pages exceed 7-8)

### Current State
Pages are manually registered in `ui/window.py`:
```python
self.batch_interface = BatchPage(self.config_manager, self)
self.addSubInterface(self.batch_interface, FluentIcon.PROJECTOR, "Generation")
```

### Problem
As the number of tools grows, `window.py` becomes cluttered with imports and registrations.

### Proposed Solution
Create a registry-based plugin system:

```python
# ui/pages/__init__.py
PAGES = [
    ("batch_page", "BatchPage", FluentIcon.PROJECTOR, "Generation"),
    ("chat_page", "ChatInterface", FluentIcon.CHAT, "Chat"),
    ("constructor_page", "ConstructorPage", FluentIcon.TILES, "Prompts Builder"),
    # New tools just add a line here
]

# ui/window.py
import importlib
from ui.pages import PAGES

for module_name, class_name, icon, title in PAGES:
    module = importlib.import_module(f"ui.pages.{module_name}")
    PageClass = getattr(module, class_name)
    page = PageClass(self.config_manager, self)
    self.addSubInterface(page, icon, title)
```

### Benefits
- Zero changes to `window.py` when adding new tools
- Clear separation of concerns
- Easy to enable/disable tools via configuration

### Implementation Trigger
Implement when total page count exceeds 7-8.

---

## UI Standardization (Technical Debt)

**Status:** Planned  
**Priority:** Low (cosmetic, not functional)

### Current State
Some UI components use manual implementations instead of native QFluentWidgets equivalents:
- `QLabel` instead of `TitleLabel`/`BodyLabel`/`CaptionLabel`
- `QFont` manual sizing instead of Fluent typography
- Hardcoded hex colors (`#ffffff`) instead of `UIConfig` constants
- Inline `setStyleSheet()` instead of `ThemeAwareBackground` pattern
- `QPushButton` instead of `PrimaryPushButton`/`TransparentPushButton`

### Problem
This leads to:
1. **Inconsistent theming** — some elements don't react to theme changes
2. **Scattered style definitions** — colors defined in multiple files
3. **Harder maintenance** — changes require hunting through codebase
4. **Visual inconsistencies** — subtle differences in spacing/fonts

### Proposed Solution
1. **Migrate all labels** → Use `TitleLabel`, `BodyLabel`, `CaptionLabel`, `SubtitleLabel`
2. **Centralize colors** → All hex codes in `UIConfig` only
3. **Use Fluent buttons** → Replace `QPushButton` with Fluent equivalents
4. **Theme subscription** → All custom widgets connect to `qconfig.themeChanged`

### Affected Files
- `ui/widgets/chat/` — bubble colors, input area
- `ui/widgets/batch/` — preview panel, status labels
- `ui/components.py` — base components
- `ui/pages/` — various pages

### Implementation Trigger
Perform during next major UI feature addition or refactor.

---

## 📜 Completed

### � BUG: Taskbar Icon Not Displayed on First Launch

**Resolved:** v1.3.1, 2026-01-20
**Original Priority:** Medium

**Problem:** The application icon does not appear in the Windows taskbar on the first launch. It only appears after restarting the application.

**Fix Applied:**
1. Updated `main.py` to use `ResourceManager.get_asset()` for retrieving the absolute path of the icon file.
2. Replaced the relative path `"assets/ico.ico"` with the absolute path resolved at runtime.

**Files Changed:** `main.py`

### 🟢 BUG: RPD Counter Not Working

**Resolved:** v1.3.1, 2026-01-20
**Original Priority:** Medium

**Problem:** The Rate Per Day counter always showed 13 regardless of actual usage. The counter should reset each calendar day. Label was also typo'd as "RDP".

**Fix Applied:** 
1. Renamed "RDP" to "RPD" in UI labels.
2. Refined `check_api_usage` and `increment_api_usage` in `batch_page.py` to be robust against missing or corrupted config data.
3. Verified daily reset logic with standalone script.

**Files Changed:** `ui/pages/batch_page.py`, `ui/widgets/batch/config_panel.py`

### 🟢 BUG: Chat Deletion Creates Infinite "New Chat" Loop

**Resolved:** 2026-01-18  
**Original Priority:** High

**Problem:** When deleting a chat, a new "New Chat" was created instead. These chats couldn't be deleted, causing infinite loop.

**Root Cause:** `delete_session()` called `start_new_chat()` which called `_refresh_sidebar()`, then `delete_session()` called `_refresh_sidebar()` again.

**Fix Applied:**
1. `delete_session()` now clears state first, then refreshes sidebar, then selects existing session or creates new as fallback
2. Added `refresh_sidebar` flag to `start_new_chat()` to skip refresh when called as fallback

**Files Changed:** `ui/pages/chat_page.py`

