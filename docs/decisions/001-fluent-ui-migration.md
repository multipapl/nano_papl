# ADR-001: Migrate to QFluentWidgets UI Framework

## Status
**Accepted** — Implemented in v2.0.0rc

## Context

### Initial State
The application was built with raw PySide6/Qt6 widgets. The UI was purely functional — technically working but visually basic. As the project matured, the need for a more polished, professional interface became apparent.

### Requirements
- Modern, premium aesthetic (Windows 11 native feel)
- Dark/light theme support with automatic switching
- Consistent design language across all components
- Minimal custom CSS/styling maintenance
- Active library with good documentation

### Options Considered
| Option | Pros | Cons |
|--------|------|------|
| **Raw PySide6** | Full control, no dependencies | High maintenance, inconsistent styling |
| **QFluentWidgets** | Native Fluent Design, theme system, rich components | Learning curve, additional dependency |
| **PyQt-Fluent-Widgets** | Similar to above | Less active, GPL license concerns |
| **Custom styling** | Unique look | Massive effort, hard to maintain |

## Decision

**Migrate entire UI layer to QFluentWidgets.**

This decision triggered a complete UI rewrite and cascading improvements:

1. **UI Rewrite** — All pages rebuilt using Fluent components (`PrimaryPushButton`, `BodyLabel`, `TreeWidget`, etc.)
2. **Theme System** — Centralized `UIConfig` for colors, `ThemeAwareBackground` base class for auto-theming
3. **Modular Architecture** — UI split into `ui/pages/` and `ui/widgets/` for better organization
4. **Core Refactoring** — Business logic decoupled from UI for testability and reuse

## Guiding Principles (Going Forward)

| Principle | Description |
|-----------|-------------|
| **Fluent-native** | Use QFluentWidgets components, avoid raw Qt widgets |
| **No hardcoding** | All colors via `UIConfig`, all sizes via constants |
| **Modularity** | Small, focused components; single responsibility |
| **Scalability** | Easy to add new pages/features without touching core |
| **Reusability** | Shared widgets in `ui/widgets/`, shared logic in `core/` |

## Consequences

### Positive ✅
- **Premium look** — App feels professional and modern
- **Faster development** — Pre-built components reduce boilerplate
- **Theme consistency** — Dark/light mode works automatically
- **Better architecture** — Forced cleanup improved overall code quality
- **Easier onboarding** — New features follow established patterns

### Negative ❌
- **Additional dependency** — ~5MB, requires `pip install qfluentwidgets`
- **Learning curve** — Fluent-specific APIs differ from standard Qt
- **Migration effort** — Required significant rewrite (one-time cost)
- **Some limitations** — Not all Qt widgets have Fluent equivalents

### Risks Mitigated
- **Library abandonment** — QFluentWidgets is actively maintained, large community
- **Performance** — No noticeable overhead in production use

## Related Decisions
- Use JSON files for chat history (simplicity over SQLite)
- Centralize constants in `core/constants.py`
- Split config into `ConfigManager` + `config_helper`
