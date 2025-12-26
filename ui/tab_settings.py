from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt
from utils import config_helper
from pathlib import Path
import os

class TabSettings(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignTop)

        # --- General Settings ---
        grp_general = QGroupBox("Global Configuration")
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # API Key
        self.entry_api_key = QLineEdit()
        self.entry_api_key.setPlaceholderText("Paste Google Gemini API Key here...")
        self.entry_api_key.setEchoMode(QLineEdit.Password) 
        self.entry_api_key.setMinimumWidth(400)
        form_layout.addRow("Google API Key:", self.entry_api_key)

        # Data Root
        self.entry_data_path = QLineEdit()
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_path)
        
        self.entry_data_path.setPlaceholderText("Default: Documents/NanoPapl")
        
        form_layout.addRow("Data Root Folder:", self.entry_data_path)
        form_layout.addRow("", btn_browse)
        
        grp_general.setLayout(form_layout)
        layout.addWidget(grp_general)

        # Save Button
        btn_save = QPushButton("SAVE SETTINGS")
        btn_save.setMinimumHeight(45)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; color: white; font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background-color: #2c974b; }
        """)
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save)

        # Info Label
        lbl_info = QLabel(
            "Note: Changing the Data Root Folder will not move existing files.\n"
            "New files (History, Images) will be saved to the new location."
        )
        lbl_info.setStyleSheet("color: #888; margin-top: 10px;")
        layout.addWidget(lbl_info)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Data Root Folder")
        if path:
            self.entry_data_path.setText(path)

    def load_settings(self):
        # API Key needs special getter for keyring
        self.entry_api_key.setText(config_helper.get_value("api_key", ""))
        
        config = config_helper.load_config()
        
        # Default path logic for display
        default_path = str(Path(os.path.expanduser("~")) / "Documents" / "NanoPapl")
        saved_path = config.get("data_root", default_path)
        self.entry_data_path.setText(saved_path)

    def save_settings(self):
        root_path = self.entry_data_path.text().strip()
        if not root_path:
             root_path = str(Path(os.path.expanduser("~")) / "Documents" / "NanoPapl")
             self.entry_data_path.setText(root_path)

        config_helper.set_value("api_key", self.entry_api_key.text().strip())
        config_helper.set_value("data_root", root_path)
        
 
        
        QMessageBox.information(self, "Saved", "Settings saved successfully!\nRestart application to apply changes.")
