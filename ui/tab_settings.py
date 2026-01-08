from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt
from core.utils import config_helper
from pathlib import Path
import os
from ui.styles import Styles
from ui.widgets.path_selector import PathSelectorWidget
from ui.base_tab import BaseTab

class TabSettings(BaseTab):
    def __init__(self):
        super().__init__()
        # Apply Global Styles
        self.setStyleSheet(Styles.GLOBAL + Styles.INPUT_FIELD + Styles.BTN_BASE)
        
        self._setup_ui()
        self._register_fields()
        self.load_state()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignTop)

        # --- General Settings ---
        grp_general = QGroupBox("Global Configuration")


        # 1. API Keys & URL (Form Layout)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # API Key
        self.entry_api_key = QLineEdit()
        self.entry_api_key.setPlaceholderText("Paste Google Gemini API Key here...")
        self.entry_api_key.setEchoMode(QLineEdit.Password) 
        self.entry_api_key.setMinimumWidth(400)
        form_layout.addRow("Google API Key:", self.entry_api_key)

        # ComfyUI API Key
        self.entry_comfy_key = QLineEdit()
        self.entry_comfy_key.setPlaceholderText("Paste ComfyUI API Key here (optional)...")
        self.entry_comfy_key.setEchoMode(QLineEdit.Password) 
        self.entry_comfy_key.setMinimumWidth(400)
        form_layout.addRow("ComfyUI API Key:", self.entry_comfy_key)

        # ComfyUI URL
        self.entry_comfy_url = QLineEdit()
        self.entry_comfy_url.setPlaceholderText("Default: http://127.0.0.1:8188")
        self.entry_comfy_url.setMinimumWidth(400)
        form_layout.addRow("ComfyUI URL:", self.entry_comfy_url)
        
        # Data Root (New Widget)
        self.path_data_root = PathSelectorWidget(
            "Data Root Folder:", 
            select_file=False, 
            dialog_title="Select Data Root Folder",
            show_label=False
        )
        form_layout.addRow("Data Root Folder:", self.path_data_root)
        
        grp_general.setLayout(form_layout)
        layout.addWidget(grp_general)

        # Save Button
        btn_save = QPushButton("SAVE SETTINGS")
        btn_save.setMinimumHeight(45)
        btn_save.setStyleSheet(Styles.BTN_PRIMARY)
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save)

        # Info Label
        lbl_info = QLabel(
            "Note: Changing the Data Root Folder will not move existing files.\n"
            "New files (History, Images) will be saved to the new location."
        )
        lbl_info.setStyleSheet("color: #888; margin-top: 10px;")
        layout.addWidget(lbl_info)
    
    def _register_fields(self):
        """Register fields with BaseTab for automated state management"""
        # Note: API keys are handled specially (keyring)
        self.register_field("comfy_url", self.entry_comfy_url)
        self.register_field("data_root", self.path_data_root)

    def load_state(self):
        """
        Override to handle special API key loading from keyring
        """
        # API Keys need special getter for keyring
        self.entry_api_key.setText(config_helper.get_value("api_key", ""))
        self.entry_comfy_key.setText(config_helper.get_value("comfy_api_key", ""))
        
        # Load other fields via BaseTab
        super().load_state()
        
        # Set defaults if fields are empty
        if not self.entry_comfy_url.text():
            self.entry_comfy_url.setText("http://127.0.0.1:8188")
        
        config = config_helper.load_config()
        if not self.path_data_root.get_path():
            default_path = str(Path(os.path.expanduser("~")) / "Documents" / "NanoPapl")
            saved_path = config.get("data_root", default_path)
            self.path_data_root.set_path(saved_path)

    def save_settings(self):
        """
        Handle saving all settings including API keys
        """
        root_path = self.path_data_root.get_path()
        if not root_path:
             root_path = str(Path(os.path.expanduser("~")) / "Documents" / "NanoPapl")
             self.path_data_root.set_path(root_path)
        
        # Comfy URL default
        c_url = self.entry_comfy_url.text().strip()
        if not c_url: c_url = "http://127.0.0.1:8188"
        self.entry_comfy_url.setText(c_url)

        # Save API keys specially (uses keyring)
        config_helper.set_value("api_key", self.entry_api_key.text().strip())
        config_helper.set_value("comfy_api_key", self.entry_comfy_key.text().strip())
        
        # Save other fields via BaseTab
        super().save_state()
        
        QMessageBox.information(self, "Saved", "Settings saved successfully!\nRestart application to apply changes.")
