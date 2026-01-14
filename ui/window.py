
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer
from qfluentwidgets import (FluentWindow, NavigationItemPosition, FluentIcon, 
                            Theme, setTheme, qconfig, ToolButton, setThemeColor)
from pathlib import Path
import os

# Import Pages
from ui.pages.settings_page import SettingsInterface
from ui.pages.chat_page import ChatInterface
from ui.pages.constructor_page import ConstructorPage
from ui.pages.tools_page import ToolsPage
from ui.pages.batch_page import BatchPage

# Import managers for dependency injection
from core.history_manager import HistoryManager
from core.utils import config_helper
from core import constants

class ModernWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(constants.WINDOW_TITLE)
        self.setWindowIcon(QIcon("assets/ico.ico"))
        self.resize(1100, 750)
        
        # Centralized initialization (Dependency Injection pattern)
        self._init_managers()
        
        # 1. Init Interfaces with dependency injection
        self.home_interface = ConstructorPage(self)
        self.tools_interface = ToolsPage(self)
        self.batch_interface = BatchPage(self)
        self.chat_interface = ChatInterface(
            history_manager=self.history_manager,
            config=self.config,
            parent=self
        )
        self.settings_interface = SettingsInterface(self)
        
        # 2. Add to Navigation (Top)
        self.addSubInterface(self.home_interface, FluentIcon.TILES, "Prompts Builder")
        self.addSubInterface(self.batch_interface, FluentIcon.PROJECTOR, "Generation")
        self.addSubInterface(self.chat_interface, FluentIcon.CHAT, "Chat")
        self.addSubInterface(self.tools_interface, FluentIcon.DEVELOPER_TOOLS, "Tools")
        
        # 3. Custom Theme Toggle (Above Settings)
        # We initialize it carefully to avoid TypeError from @overload
        self.theme_toggle = ToolButton(self.navigationInterface)
        self.theme_toggle.setIcon(FluentIcon.BRIGHTNESS)
        self.theme_toggle.isSelectable = False  # Skip NavigationPanel focus
        self.theme_toggle.setToolTip("Toggle Theme")
        
        self.navigationInterface.addWidget(
            routeKey='themeToggle',
            widget=self.theme_toggle,
            onClick=self._toggle_theme,
            position=NavigationItemPosition.BOTTOM
        )
        
        # 4. Settings (Bottom-most)
        self.addSubInterface(self.settings_interface, FluentIcon.SETTING, "Settings", NavigationItemPosition.BOTTOM)
        
        # Init icon state and subscribe to changes
        self._on_theme_changed(qconfig.theme)
        qconfig.themeChanged.connect(self._on_theme_changed)
        
        # Set default startup page (Timer used to ensure NavigationPanel is ready)
        QTimer.singleShot(0, lambda: self.switchTo(self.batch_interface))

    def _on_theme_changed(self, theme):
        """Update the sidebar icon based on current theme"""
        # Toggle icon logic: Show 'Moon' (QUIET_HOURS) when Light, 'Sun' (BRIGHTNESS) when Dark
        # BRIGHTNESS = Sun, QUIET_HOURS = Moon
        icon = FluentIcon.BRIGHTNESS if theme == Theme.DARK else FluentIcon.QUIET_HOURS
        self.theme_toggle.setIcon(icon)

    def _toggle_theme(self):
        """Invoke toggle with a tiny delay to avoid collision with nav panel logic"""
        QTimer.singleShot(0, self._do_toggle_theme)

    def _do_toggle_theme(self):
        """Actual global theme toggle logic"""
        new_theme = Theme.LIGHT if qconfig.theme == Theme.DARK else Theme.DARK
        setTheme(new_theme)
        
        # Respect accent colors from Settings logic
        if new_theme == Theme.DARK:
            saved_color = config_helper.get_value("theme_color_dark", "#4cc2ff")
        else:
            saved_color = config_helper.get_value("theme_color_light", "#0078d4")
            
        setThemeColor(saved_color)
        qconfig.themeChanged.emit(new_theme)
    
    def _init_managers(self) -> None:
        """Initialize shared managers (Dependency Injection pattern)"""
        self.config = config_helper.load_config()
        
        default_root = Path(os.path.expanduser("~")) / "Documents" / constants.APP_NAME.replace(" ", "")
        root_path = Path(self.config.get("data_root", str(default_root)))
        
        hist_path = root_path / "History"
        self.history_manager = HistoryManager(base_dir=hist_path)
