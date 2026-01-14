import json
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import Signal
from qfluentwidgets import (
    BodyLabel, ComboBox, PushButton, TransparentPushButton, 
    FluentIcon, MessageBox
)
from ui.components import InputDialog

class ModernPresetToolbar(QWidget):
    """Modern version of PresetToolbarWidget using qfluentwidgets."""
    preset_loaded = Signal(dict)
    save_requested = Signal(str)
    reset_requested = Signal()

    def __init__(self, presets_file: str, show_reset: bool = True, reset_label: str = "Reset All Defaults", parent=None):
        super().__init__(parent)
        self.presets_file = presets_file
        self.show_reset = show_reset
        self.reset_label = reset_label
        self._setup_ui()
        self.refresh_presets()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        layout.addWidget(BodyLabel("Presets:"))

        self.combo = ComboBox()
        self.combo.setMinimumWidth(200)
        layout.addWidget(self.combo)

        self.btn_load = PushButton("Load")
        self.btn_load.clicked.connect(self._on_load)
        layout.addWidget(self.btn_load)

        self.btn_save = PushButton("Save As...")
        self.btn_save.clicked.connect(self._on_save_request)
        layout.addWidget(self.btn_save)

        self.btn_del = TransparentPushButton(FluentIcon.DELETE, "Delete")
        self.btn_del.clicked.connect(self._on_delete)
        layout.addWidget(self.btn_del)

        layout.addStretch()

        if self.show_reset:
            self.btn_reset = PushButton(self.reset_label)
            self.btn_reset.clicked.connect(self.reset_requested.emit)
            layout.addWidget(self.btn_reset)

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
        dialog = InputDialog("Save Preset", "Enter preset name:", self)
        if dialog.exec():
            name = dialog.text()
            if name:
                self.save_requested.emit(name)

    def _on_delete(self):
        name = self.combo.currentText()
        if not name: return
        
        dialog = MessageBox("Delete Preset", f"Are you sure you want to delete '{name}'?", self)
        if dialog.exec():
            presets = self._load_from_file()
            if name in presets:
                del presets[name]
                self._save_to_file(presets)
                self.refresh_presets()

    def save_preset_data(self, name: str, data: dict):
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
            except Exception: return {}
        return {}

    def _save_to_file(self, presets: dict):
        with open(self.presets_file, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=4, ensure_ascii=False)
