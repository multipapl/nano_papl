# 📚 Documentation Index

Use this file as a reference to access project documentation.

## Quick Reference

| Document | Description | When to Use |
|----------|-------------|-------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | High-level system design, data flow, key classes | Understanding codebase structure |
| [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) | Setup, coding standards, workflows | Contributing, onboarding |
| [FUTURE_PLAN.md](./FUTURE_PLAN.md) | Backlog, bugs, planned features | Tracking tasks, history |
| [TEST_COVERAGE.md](./TEST_COVERAGE.md) | Test structure, coverage status | Writing/running tests |
| [decisions/](./decisions/) | Architecture Decision Records (ADRs) | Understanding *why* decisions were made |

## Key Directories

```
nano_papl/
├── core/           # Business logic, workers, services
├── ui/             # PySide6 + QFluentWidgets UI
│   ├── pages/      # Main page components
│   ├── widgets/    # Reusable widgets
│   └── components.py  # Base UI components
├── tests/          # Pytest test suite
└── docs/           # This documentation
```

## When to Reference

- **New feature?** → Start with `ARCHITECTURE.md` for context
- **Bug fix?** → Check `FUTURE_PLAN.md` for related issues
- **Writing tests?** → See `TEST_COVERAGE.md`
- **Code style questions?** → `DEVELOPMENT_GUIDE.md`
