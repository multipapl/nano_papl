# 🔮 Future Development Plan

This document outlines planned architectural improvements for Nano Papl.

---

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
