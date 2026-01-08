# 🏗️ UI Modularization & Refactoring Plan

**Objective**: Transition the Nano Papl UI from a monolithic "script-based" layout to a modern, **Component-Based Architecture**.

## 🛑 Current State (The Problem)
Currently, each Tab file (e.g., `tab_batch.py`) defines its entire interface methodically in one giant `_setup_ui()` function.
*   **Rigidity**: Moving a "File Selector" from Batch to Settings requires copy-pasting code and logic.
*   **Hardcoded Layouts**: Lots of `setFixedSize`, manual margins, and fragile `HBox`/`VBox` nestings that break on different screen sizes.
*   **Duplication**: Logic for "Browse" buttons or "Save Presets" is repeated across tabs.

## ✅ Target State (The Solution)
We will treat the UI like **LEGO**. We will build small, smart, self-contained "Widgets" in a separate folder, and then simply assemble them in the Tabs.

### Directory Structure
```
ui/
├── styles.py           # (Already Done) Colors & Fonts
├── widgets/            # [NEW] Reusable Components
│   ├── __init__.py
│   ├── file_selector.py    # Label + Input + Browse Button
│   ├── console_log.py      # Black text area for logs
│   ├── preset_bar.py       # Dropdown + Load/Save/Delete
│   ├── image_preview.py    # Auto-resizing image container
│   └── ...
├── tab_batch.py        # Becomes just a container for widgets
├── tab_chat.py
└── ...
```

## 📋 Component Inventory (Todo List)

### Phase 1: Foundation & Generic Widgets
These are used everywhere. Implementing them fixes 50% of the verbosity.

- [x] **`PathSelectorWidget`**
    -   *Inputs*: Label text (e.g., "Input Folder"), Mode (File vs Folder), Config Key (for auto-save).
    -   *Features*: Drag & Drop built-in, "Browse" button pre-wired to `QFileDialog`.
    -   *Usage*: `layout.addWidget(PathSelectorWidget("Input Root", config_key="input_path"))`

- [x] **`ConsoleLogWidget`**
    -   *Inputs*: Initial text.
    -   *Features*: Pre-styled black background, monospace font, `append_log(msg)` method.

- [x] **`ActionHeaderWidget`**
    -   *Inputs*: Title, Optional "Reset" button.
    -   *Features*: Standardized H1-style headers with specific spacing.

### Phase 2: Functional Logic Widgets
These contain some business logic but are strictly UI controllers.

- [x] **`PresetToolbarWidget`**
    -   *Features*: ComboBox for presets, buttons for "Load", "Save As", "Delete".
    -   *Signals*: Emits `presetChanged(data)`.

- [x] **`ImageCompareWidget`** (For Batch Tab)
    -   *Features*: "Before" and "After" image slots, resizing logic, central arrow.

- [x] **`SeasonsTreeWidget`**
    -   *Features*: Encapsulates the Season/Light tree logic, data extraction, and restoration.

### Phase 3: Tab Assembly (Refactoring)
Once widgets exist, we rewrite the Tabs to use them.

1.  [x] **Refactor `tab_settings.py`**: It's the simplest. Replace manual file inputs with `PathSelectorWidget`.
2.  [x] **Refactor `tab_batch.py`**: Replace the massive "Paths" group with 3-4 lines of widget instantiation.
3.  [x] **Refactor `tab_constructor.py`**: Use `PresetToolbarWidget`.

## 📐 Responsiveness & Styling Rules
To ensure "Adapts to anything" behavior:
1.  **Avoid `setFixedSize`**: Use `setMinimumSize` or `setMaximumSize` only when physically necessary.
2.  **Use `QSizePolicy`**: Teach widgets how to grow.
    -   *Input Fields*: Grow Horizontally.
    -   *Logs/Chats*: Grow in All Directions.
    -   *Buttons*: Fixed Height, Variable Width (or Fixed Width for icons).
3.  **Layouts**: Use `QGridLayout` for forms (labels aligned with inputs) instead of nested HBoxes.

## 🚀 Execution Strategy for Next Session
1.  Create `ui/widgets/` folder.
2.  Implement `PathSelectorWidget` as the Proof-of-Concept.
3.  Replace the manual path selection in `TabSettings` with this new widget.
4.  Verify that it works, looks good, and saves code.
5.  Repeat for other components.
