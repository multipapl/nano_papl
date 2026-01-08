from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton, 
    QMessageBox, QInputDialog, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
import json
import os
from ui.styles import Styles, Colors

class PresetToolbarWidget(QWidget):
    """
    A generic toolbar for managing presets (Load, Save, Delete).
    Handles JSON file IO internally.
    Signals:
        - preset_loaded(dict): Emitted when a preset is loaded.
        - save_requested(str): Emitted when user clicks save and provides a name. 
                               Parent should call save_preset_data(name, data).
        - reset_requested(): Emitted when the optional reset button is clicked.
    """
    preset_loaded = Signal(dict)
    save_requested = Signal(str)
    reset_requested = Signal()

    def __init__(self, presets_file: str, show_reset: bool = True, reset_label: str = "Reset All Defaults"):
        super().__init__()
        self.presets_file = presets_file
        self.show_reset = show_reset
        self.reset_label = reset_label
        
        self.setStyleSheet(Styles.GLOBAL + Styles.INPUT_FIELD + Styles.BTN_BASE)
        self._setup_ui()
        self.refresh_presets()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Label
        layout.addWidget(QLabel("Presets:"))

        # Combo
        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        layout.addWidget(self.combo)

        # Load
        btn_load = QPushButton("Load")
        btn_load.clicked.connect(self._on_load)
        layout.addWidget(btn_load)

        # Save
        btn_save = QPushButton("Save As...")
        btn_save.clicked.connect(self._on_save_request)
        layout.addWidget(btn_save)

        # Delete
        btn_del = QPushButton("Delete")
        btn_del.setStyleSheet(f"""
            QPushButton {{ 
                background-color: transparent; 
                border: 1px solid {Colors.DANGER}; 
                color: {Colors.DANGER}; 
                border-radius: 6px; padding: 5px 10px; 
            }}
            QPushButton:hover {{ background-color: {Colors.DANGER}; color: white; }}
        """)
        btn_del.clicked.connect(self._on_delete)
        layout.addWidget(btn_del)

        # Spacer
        layout.addStretch()

        # Optional Reset
        if self.show_reset:
            btn_reset = QPushButton(self.reset_label)
            btn_reset.setStyleSheet(Styles.BTN_DANGER)
            btn_reset.clicked.connect(self.reset_requested.emit)
            layout.addWidget(btn_reset)

    def refresh_presets(self):
        self.combo.clear()
        presets = self._load_from_file()
        self.combo.addItems(sorted(presets.keys()))

    def _on_load(self):
        name = self.combo.currentText()
        if not name: return
        
        presets = self._load_from_file()
        if name in presets:
            self.preset_loaded.emit(presets[name])

    def _on_save_request(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        if ok and name.strip():
            self.save_requested.emit(name.strip())

    def _on_delete(self):
        name = self.combo.currentText()
        if not name: return
        
        reply = QMessageBox.question(
            self, "Delete Preset", 
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            presets = self._load_from_file()
            if name in presets:
                del presets[name]
                self._save_to_file(presets)
                self.refresh_presets()

    def save_preset_data(self, name: str, data: dict):
        """
        Public method to be called by parent after receiving save_requested.
        """
        presets = self._load_from_file()
        presets[name] = data
        self._save_to_file(presets)
        self.refresh_presets()
        self.combo.setCurrentText(name)

    def _load_from_file(self) -> dict:
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_to_file(self, presets: dict):
        with open(self.presets_file, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=4, ensure_ascii=False)
