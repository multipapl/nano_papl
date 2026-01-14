from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
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
from ui.components import ModernPathSelector, CustomColorSettingCard, get_scroll_style, MessageBox

class SettingsInterface(QWidget):
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
        self.scroll.setStyleSheet(get_scroll_style())
        
        self.container = QWidget()
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
        font.setPixelSize(22)
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
        
        btn = PrimaryPushButton(FluentIcon.SAVE, "Save Key")
        btn.clicked.connect(self.save_api_key)
        self.api_key_card.viewLayout.addWidget(self.api_key_input)
        self.api_key_card.viewLayout.addWidget(btn)
        
        # ComfyUI Key
        self.comfy_key_card = ExpandSettingCard(
            FluentIcon.VPN, "ComfyUI API Key",
            "Configure your ComfyUI API access key (optional)", self
        )
        self.comfy_key_input = LineEdit()
        self.comfy_key_input.setPlaceholderText("Enter Key...")
        self.comfy_key_input.setText(config_helper.get_value("comfy_api_key", ""))
        self.comfy_key_input.setEchoMode(LineEdit.Password)
        
        btn_c = PrimaryPushButton(FluentIcon.SAVE, "Save Key")
        btn_c.clicked.connect(self.save_comfy_api_key)
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
        group.addSettingCard(self.theme_card)

        # Color
        dark = isDarkTheme()
        saved_color = config_helper.get_value("theme_color_dark" if dark else "theme_color_light", 
                                              "#4cc2ff" if dark else "#0078d4")
        self.color_card = CustomColorSettingCard(
            QColor(saved_color), FluentIcon.PALETTE,
            "Theme Color", "Accent color for the current theme", self
        )
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
        
        btn = PrimaryPushButton(FluentIcon.SAVE, "Save URL")
        btn.clicked.connect(self.save_comfy_url)
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
        btn = PrimaryPushButton(FluentIcon.SAVE, "Save Path")
        btn.clicked.connect(self.save_data_root)
        
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
        self.cache_card.hBoxLayout.addWidget(btn_cache, 0, Qt.AlignRight)
        self.cache_card.hBoxLayout.addSpacing(16)
        
        # Images
        self.images_card = SettingCard(FluentIcon.PHOTO, "Delete Output Images", "Permanently delete all generated images", self)
        btn_imgs = PrimaryPushButton("Delete Images")
        btn_imgs.setFixedWidth(120)
        btn_imgs.clicked.connect(self.delete_generated_images)
        self.images_card.hBoxLayout.addWidget(btn_imgs, 0, Qt.AlignRight)
        self.images_card.hBoxLayout.addSpacing(16)
        
        group.addSettingCard(self.cache_card)
        group.addSettingCard(self.images_card)
        self.layout.addWidget(group)

    # --- Actions ---

    def save_api_key(self):
        config_helper.set_value("api_key", self.api_key_input.text().strip())
        self._show_success("Gemini API Key saved")

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
        
        color_key = "theme_color_dark" if checked else "theme_color_light"
        def_color = "#4cc2ff" if checked else "#0078d4"
        saved_color = config_helper.get_value(color_key, def_color)
        
        setThemeColor(saved_color)
        self.color_card.colorPicker.setColor(QColor(saved_color))
        qconfig.themeChanged.emit(new_theme)

    def on_color_changed(self, color):
        setThemeColor(color)
        key = "theme_color_dark" if isDarkTheme() else "theme_color_light"
        config_helper.set_value(key, color.name())
        qconfig.themeChanged.emit(qconfig.theme)

    def reset_theme_color(self):
        default = "#4cc2ff" if isDarkTheme() else "#0078d4"
        self.on_color_changed(QColor(default))
        self.color_card.colorPicker.setColor(QColor(default))

    def _sync_theme_switch(self):
        self.theme_card.switchButton.blockSignals(True)
        self.theme_card.switchButton.setChecked(isDarkTheme())
        self.theme_card.switchButton.blockSignals(False)
        self.scroll.setStyleSheet(get_scroll_style())
        
        dark = isDarkTheme()
        saved = config_helper.get_value("theme_color_dark" if dark else "theme_color_light", 
                                       "#4cc2ff" if dark else "#0078d4")
        self.color_card.colorPicker.setColor(QColor(saved))

    def _show_success(self, text):
        InfoBar.success("Success", text, parent=self, duration=2000, position=InfoBarPosition.TOP)
