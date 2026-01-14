# 🐙 Git Workflow Guide (Solo Developer)

This guide helps keep the project history clean and releases organized for a single developer.

---

## 1. Daily Development (Branch `dev`)

Use the `dev` branch for all active work. Frequent, descriptive commits are encouraged.

```bash
# Switching to dev
git checkout dev

# Daily cycle
git add .
git commit -m "feat: added new message grouping logic"
# ... more work ...
git commit -m "fix: corrected bubble alignment in dark mode"
```

---

## 2. Release Procedure

When a version is ready for release (e.g., `v1.3.0`):

1.  **Version Bump**: Update the version constant in `core/constants.py`.
2.  **Build**: Generate the executable using the build script.
3.  **Merge to Main**: Use **Squash** to keep `main` history clean.

```bash
git checkout main
git merge --squash dev
git commit -m "Release v1.3.0: Modular UI Refactor & Quality improvements"
git tag v1.3.0
git push origin main --tags
```

---

## 3. GitHub Releases

1.  Create a **Draft Release** on GitHub using the new tag.
2.  Attach the generated ZIP/EXE.
3.  Summarize key changes from the `CHANGELOG.md` (if applicable).
4.  Once verified, hit **Publish**.

---

## 4. Commit Message Standard (Optional but Recommended)

- `feat:`: New feature.
- `fix:`: Bug fix.
- `refactor:`: Code change that neither fixes a bug nor adds a feature.
- `docs:`: Documentation changes.
- `perf:`: Performance improvements.
