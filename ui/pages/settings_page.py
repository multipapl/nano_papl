from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal, QSize
from pathlib import Path
import os
import shutil

from qfluentwidgets import (
    SwitchButton, Theme, setTheme, FluentIcon, SettingCardGroup, 
    SwitchSettingCard, isDarkTheme, LineEdit, PrimaryPushButton, 
    InfoBar, InfoBarPosition, ExpandSettingCard, ColorPickerButton, SettingCard,
    setThemeColor, qconfig, ToolButton, ScrollArea
)

from core.utils import config_helper
from core import constants
from core.utils.path_provider import PathProvider
from ui.components import (
    ModernPathSelector, CustomColorSettingCard, get_scroll_style, 
    MessageBox, ThemeAwareBackground, UIConfig
)

class SettingsInterface(ThemeAwareBackground):
    """
    Modular Settings Interface for the application.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsInterface")
        self._init_ui()
        
    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Use ScrollArea for settings
        self.scroll = ScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.viewport().setStyleSheet("background: transparent;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # 1. Title
        self._init_title()
        
        # 2. Settings Groups
        self._init_api_group()
        self._init_appearance_group()
        self._init_comfy_group()
        self._init_storage_group()
        self._init_maintenance_group()
        
        self.layout.addStretch(1)
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)
        
        # Initial state sync
        qconfig.themeChanged.connect(self._sync_theme_switch)

    def _init_title(self):
        title = QLabel("Settings")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        self.layout.addWidget(title)
        self.layout.addSpacing(10)

    def _init_api_group(self):
        group = SettingCardGroup("API Configuration", self.container)
        
        # Gemini
        self.api_key_card = ExpandSettingCard(
            FluentIcon.DEVELOPER_TOOLS, "Gemini API Key",
            "Configure your Google Gemini API access key", self
        )
        self.api_key_input = LineEdit()
        self.api_key_input.setPlaceholderText("Enter Key...")
        self.api_key_input.setText(config_helper.get_value("api_key", ""))
        self.api_key_input.setEchoMode(LineEdit.Password)
        self.api_key_input.setToolTip("Enter your Google Gemini API key for cloud generation.")
        
        btn_save = PrimaryPushButton(FluentIcon.SAVE, "Save Key")
        btn_save.clicked.connect(self.save_api_key)
        btn_save.setToolTip("Permanently save the Gemini API key to your local configuration.")
        
        btn_refresh = ToolButton(FluentIcon.SYNC, self)
        btn_refresh.setToolTip("Refresh from secure storage")
        btn_refresh.clicked.connect(self.refresh_api_key)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.api_key_input, 1)
        h_layout.addWidget(btn_refresh)
        
        self.api_key_card.viewLayout.addLayout(h_layout)
        self.api_key_card.viewLayout.addWidget(btn_save)
        
        # ComfyUI Key
        self.comfy_key_card = ExpandSettingCard(
            FluentIcon.VPN, "ComfyUI API Key",
            "Configure your ComfyUI API access key (optional)", self
        )
        self.comfy_key_input = LineEdit()
        self.comfy_key_input.setPlaceholderText("Enter Key...")
        self.comfy_key_input.setText(config_helper.get_value("comfy_api_key", ""))
        self.comfy_key_input.setEchoMode(LineEdit.Password)
        self.comfy_key_input.setToolTip("Enter your ComfyUI API key (if required by your custom backend).")
        
        btn_c = PrimaryPushButton(FluentIcon.SAVE, "Save Key")
        btn_c.clicked.connect(self.save_comfy_api_key)
        btn_c.setToolTip("Save the ComfyUI API key.")
        self.comfy_key_card.viewLayout.addWidget(self.comfy_key_input)
        self.comfy_key_card.viewLayout.addWidget(btn_c)

        group.addSettingCard(self.api_key_card)
        group.addSettingCard(self.comfy_key_card)
        self.layout.addWidget(group)

    def _init_appearance_group(self):
        group = SettingCardGroup("Appearance", self.container)
        
        self.theme_card = SwitchSettingCard(
            FluentIcon.BRUSH, "Dark Theme",
            "Toggle between Light and Dark modes", None, self
        )
        self.theme_card.switchButton.setChecked(isDarkTheme())
        self.theme_card.switchButton.checkedChanged.connect(self.toggle_theme)
        self.theme_card.switchButton.setToolTip("Toggle between system-wide Light and Dark interface themes.")
        group.addSettingCard(self.theme_card)

        # Color
        saved_color = config_helper.get_value("theme_color", 
                                              config_helper.get_value("theme_color_dark" if isDarkTheme() else "theme_color_light", 
                                                                     UIConfig.ACCENT_DEFAULT_DARK if isDarkTheme() else UIConfig.ACCENT_DEFAULT_LIGHT))
        self.color_card = CustomColorSettingCard(
            QColor(saved_color), FluentIcon.PALETTE,
            "Theme Color", "Accent color for the current theme", self
        )
        self.color_card.colorPicker.setToolTip("Select a custom accent color for the interface.")
        self.color_card.btnReset.setToolTip("Restore the default accent color for the active theme.")
        self.color_card.colorChanged.connect(self.on_color_changed)
        self.color_card.btnReset.clicked.connect(self.reset_theme_color)
        group.addSettingCard(self.color_card)
        
        self.layout.addWidget(group)

    def _init_comfy_group(self):
        group = SettingCardGroup("ComfyUI Integration", self.container)
        self.comfy_url_card = ExpandSettingCard(
            FluentIcon.LINK, "ComfyUI URL",
            "Set the backend URL for local generation", self
        )
        self.comfy_url_input = LineEdit()
        self.comfy_url_input.setText(config_helper.get_value("comfy_url", constants.DEFAULT_COMFY_URL))
        self.comfy_url_input.setToolTip("The local or network address of your ComfyUI server (e.g., http://127.0.0.1:8188).")
        
        btn = PrimaryPushButton(FluentIcon.SAVE, "Save URL")
        btn.clicked.connect(self.save_comfy_url)
        btn.setToolTip("Update the ComfyUI backend connection address.")
        self.comfy_url_card.viewLayout.addWidget(self.comfy_url_input)
        self.comfy_url_card.viewLayout.addWidget(btn)
        
        group.addSettingCard(self.comfy_url_card)
        self.layout.addWidget(group)

    def _init_storage_group(self):
        group = SettingCardGroup("Storage & Data", self.container)
        self.data_root_card = ExpandSettingCard(
            FluentIcon.FOLDER, "Data Root Folder",
            "Where history and generated images are stored", self
        )
        def_root = str(PathProvider().get_default_projects_path()) if hasattr(PathProvider, 'get_default_projects_path') else ""
        current = config_helper.get_value("data_root", def_root)
        
        self.data_root_selector = ModernPathSelector("Path:", current, select_file=False)
        self.data_root_selector.setToolTip("Select a base folder for projects, history, and generated outputs.")
        btn = PrimaryPushButton(FluentIcon.SAVE, "Save Path")
        btn.clicked.connect(self.save_data_root)
        btn.setToolTip("Apply and save the new data root path.")
        
        self.data_root_card.viewLayout.addWidget(self.data_root_selector)
        self.data_root_card.viewLayout.addWidget(btn)
        group.addSettingCard(self.data_root_card)
        self.layout.addWidget(group)

    def _init_maintenance_group(self):
        group = SettingCardGroup("Maintenance", self.container)
        
        # Cache
        self.cache_card = SettingCard(FluentIcon.DELETE, "Clear App Cache", "Delete temp files and logs", self)
        btn_cache = PrimaryPushButton("Clear Cache")
        btn_cache.setFixedWidth(120)
        btn_cache.clicked.connect(self.clear_app_cache)
        btn_cache.setToolTip("Delete all temporary generation files and application logs to free up space.")
        self.cache_card.hBoxLayout.addWidget(btn_cache, 0, Qt.AlignRight)
        self.cache_card.hBoxLayout.addSpacing(16)
        
        # Images
        self.images_card = SettingCard(FluentIcon.PHOTO, "Delete Output Images", "Permanently delete all generated images", self)
        btn_imgs = PrimaryPushButton("Delete Images")
        btn_imgs.setFixedWidth(120)
        btn_imgs.clicked.connect(self.delete_generated_images)
        btn_imgs.setToolTip("Permanently delete all images in the generated outputs folder.")
        self.images_card.hBoxLayout.addWidget(btn_imgs, 0, Qt.AlignRight)
        self.images_card.hBoxLayout.addSpacing(16)
        
        group.addSettingCard(self.cache_card)
        group.addSettingCard(self.images_card)
        self.layout.addWidget(group)

    # --- Actions ---

    def save_api_key(self):
        key = self.api_key_input.text().strip()
        if not key:
            InfoBar.warning("Warning", "API Key cannot be empty", parent=self, position=InfoBarPosition.TOP)
            return
            
        # Basic validation for Gemini keys (typically ~39 characters)
        if len(key) < 30:
            InfoBar.warning("Suspicious Key", f"The entered key seems too short ({len(key)} chars). Gemini keys are usually ~39 chars.", 
                           parent=self, duration=5000, position=InfoBarPosition.TOP)
        elif len(key) > 50:
            InfoBar.warning("Suspicious Key", f"The entered key seems too long ({len(key)} chars). Gemini keys are usually ~39 chars.", 
                           parent=self, duration=5000, position=InfoBarPosition.TOP)
            
        config_helper.set_value("api_key", key)
        self._show_success(f"Gemini API Key saved (Length: {len(key)})")

    def refresh_api_key(self):
        """Force a re-read from the secure storage."""
        # We bypass get_value to ensure we aren't just hitting a stale cache if something changed externally
        import keyring
        try:
            val = keyring.get_password(constants.KEYRING_SERVICE_NAME, constants.CONFIG_KEY_API_KEY)
            if val:
                val = val.strip()
                self.api_key_input.setText(val)
                self._show_success("API Key successfully synchronized from storage")
            else:
                InfoBar.warning("Not Found", "API Key was not found in secure storage.", parent=self, position=InfoBarPosition.TOP)
        except Exception as e:
            InfoBar.error("Keyring Error", str(e), parent=self, position=InfoBarPosition.TOP)

    def save_comfy_api_key(self):
        config_helper.set_value("comfy_api_key", self.comfy_key_input.text().strip())
        self._show_success("ComfyUI API Key saved")

    def save_comfy_url(self):
        url = self.comfy_url_input.text().strip() or constants.DEFAULT_COMFY_URL
        config_helper.set_value("comfy_url", url)
        self._show_success("ComfyUI URL saved")

    def save_data_root(self):
        root = self.data_root_selector.get_path()
        if root:
            config_helper.set_value("data_root", root)
            self._show_success("Data Root updated")

    def clear_app_cache(self):
        if MessageBox("Clear Cache", "Delete all temporary files and logs?", self).exec():
            try:
                temp_dir = PathProvider().get_temp_dir()
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    temp_dir.mkdir()
                self._show_success("Cache cleared")
            except Exception as e:
                InfoBar.error("Error", str(e), self)

    def delete_generated_images(self):
        if MessageBox("Delete Images", "Delete ALL generated images permanently?", self).exec():
            try:
                root = Path(config_helper.get_value("data_root", ""))
                img_dir = root / constants.GENERATED_IMAGES_DIR_NAME
                if img_dir.exists():
                    shutil.rmtree(img_dir)
                    img_dir.mkdir()
                self._show_success("Images deleted")
            except Exception as e:
                InfoBar.error("Error", str(e), self)

    def toggle_theme(self, checked):
        new_theme = Theme.DARK if checked else Theme.LIGHT
        setTheme(new_theme)
        
        # maintain existing accent color when toggling theme
        current_color = self.color_card.colorPicker.color
        setThemeColor(current_color)
        
        qconfig.themeChanged.emit(new_theme)

    def on_color_changed(self, color):
        setThemeColor(color)
        config_helper.set_value("theme_color", color.name())
        qconfig.themeChanged.emit(qconfig.theme)

    def reset_theme_color(self):
        dark = isDarkTheme()
        default = UIConfig.ACCENT_DEFAULT_DARK if dark else UIConfig.ACCENT_DEFAULT_LIGHT
        self.on_color_changed(QColor(default))
        self.color_card.colorPicker.setColor(QColor(default))

    def _sync_theme_switch(self):
        self.theme_card.switchButton.blockSignals(True)
        self.theme_card.switchButton.setChecked(isDarkTheme())
        self.theme_card.switchButton.blockSignals(False)
        self.scroll.setStyleSheet(get_scroll_style())
        
        dark = isDarkTheme()
        saved = config_helper.get_value("theme_color", 
                                       config_helper.get_value("theme_color_dark" if dark else "theme_color_light", 
                                                              UIConfig.ACCENT_DEFAULT_DARK if dark else UIConfig.ACCENT_DEFAULT_LIGHT))
        self.color_card.colorPicker.setColor(QColor(saved))

    def _show_success(self, text):
        InfoBar.success("Success", text, parent=self, duration=2000, position=InfoBarPosition.TOP)
