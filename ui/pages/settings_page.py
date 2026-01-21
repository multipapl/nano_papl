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
    MessageBox, UIConfig, NPBasePage
)

class SettingsInterface(NPBasePage):
    """
    Modular Settings Interface for the application.
    Refactored to inherit from NPBasePage.
    """
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsInterface")
        self.config_manager = config_manager
        self._init_ui()
        
    def _init_ui(self):
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
        
        # Use NPBasePage utility
        self.scroll = self.addScrollArea(self.container)
        
        # Initial state sync
        qconfig.themeChanged.connect(self._sync_theme_switch)

    def _init_title(self):
        from qfluentwidgets import TitleLabel
        self.title_label = TitleLabel("Settings")
        self.layout.addWidget(self.title_label)
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
        self.api_key_input.setText(self.config_manager.config.api_key)
        self.api_key_input.setEchoMode(LineEdit.Password) # Hidden by default
        self.api_key_input.setToolTip("Enter your Google Gemini API key for cloud generation.")
        
        # Visibility Toggle
        self.btn_visibility = ToolButton(FluentIcon.VIEW, self)
        self.btn_visibility.setToolTip("Show/Hide Key")
        self.btn_visibility.clicked.connect(self.toggle_api_visibility)
        
        btn_save = PrimaryPushButton(FluentIcon.SAVE, "Save Key")
        btn_save.clicked.connect(self.save_api_key)
        btn_save.setToolTip("Permanently save the Gemini API key to your local configuration.")
        
        btn_refresh = ToolButton(FluentIcon.SYNC, self)
        btn_refresh.setToolTip("Refresh from secure storage")
        btn_refresh.clicked.connect(self.refresh_api_key)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.api_key_input, 1)
        h_layout.addWidget(self.btn_visibility)
        h_layout.addWidget(btn_refresh)
        
        self.api_key_card.viewLayout.addLayout(h_layout)
        self.api_key_card.viewLayout.addWidget(btn_save)

        # Timeout Logic
        from qfluentwidgets import SpinBox
        self.timeout_card = SettingCard(
            FluentIcon.SPEED_HIGH, "API Timeout",
            "Maximum time (seconds) to wait for generation response", self
        )
        self.timeout_spin = SpinBox()
        self.timeout_spin.setRange(30, 3600) # 30s to 1 hour
        self.timeout_spin.setValue(self.config_manager.config.api_timeout)
        self.timeout_spin.setToolTip("Set connection timeout in seconds (Default: 600)")
        
        btn_tout = PrimaryPushButton(FluentIcon.SAVE, "Save")
        btn_tout.setFixedWidth(80)
        btn_tout.clicked.connect(self.save_timeout)
        
        self.timeout_card.hBoxLayout.addWidget(self.timeout_spin, 0, Qt.AlignRight)
        self.timeout_card.hBoxLayout.addSpacing(10)
        self.timeout_card.hBoxLayout.addWidget(btn_tout, 0, Qt.AlignRight)
        self.timeout_card.hBoxLayout.addSpacing(16)
        
        group.addSettingCard(self.api_key_card)
        group.addSettingCard(self.timeout_card)
        self.comfy_key_card = ExpandSettingCard(
            FluentIcon.VPN, "ComfyUI API Key",
            "Configure your ComfyUI API access key (optional)", self
        )
        self.comfy_key_input = LineEdit()
        self.comfy_key_input.setPlaceholderText("Enter Key...")
        self.comfy_key_input.setText(self.config_manager.config.comfy_api_key)
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
        saved_color = self.config_manager.config.theme_color or (
            UIConfig.ACCENT_DEFAULT_DARK if isDarkTheme() else UIConfig.ACCENT_DEFAULT_LIGHT
        )
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
        self.comfy_url_input.setText(self.config_manager.config.comfy_url or constants.DEFAULT_COMFY_URL)
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
        current = self.config_manager.config.data_root or def_root
        
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

    def toggle_api_visibility(self):
        if self.api_key_input.echoMode() == LineEdit.Password:
            self.api_key_input.setEchoMode(LineEdit.Normal)
            self.btn_visibility.setIcon(FluentIcon.HIDE)
        else:
            self.api_key_input.setEchoMode(LineEdit.Password)
            self.btn_visibility.setIcon(FluentIcon.VIEW)

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
            
        self.config_manager.save()
        self._show_success(f"Gemini API Key saved (Length: {len(key)})")

    def save_timeout(self):
        val = self.timeout_spin.value()
        self.config_manager.config.api_timeout = val
        self.config_manager.save()
        self._show_success(f"Timeout updated to {val} seconds")

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
        self.config_manager.config.comfy_api_key = self.comfy_key_input.text().strip()
        self.config_manager.save()
        self._show_success("ComfyUI API Key saved")

    def save_comfy_url(self):
        url = self.comfy_url_input.text().strip() or constants.DEFAULT_COMFY_URL
        self.config_manager.config.comfy_url = url
        self.config_manager.save()
        self._show_success("ComfyUI URL saved")

    def save_data_root(self):
        root = self.data_root_selector.get_path()
        if root:
            self.config_manager.config.data_root = root
            self.config_manager.save()
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
                root = Path(self.config_manager.config.data_root or "")
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
        self.config_manager.config.theme_color = color.name()
        self.config_manager.save()
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
        self.showInfoBar("Success", text)
