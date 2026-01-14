from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import FluentIcon, ToolButton
from ui.widgets.chat import ChatMessageArea
from ui.components import ThemeAwareBackground

class ChatMessageDisplay(ThemeAwareBackground):
    """
    Modular component for displaying chat messages and the header.
    """
    toggleSidebarRequested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 1. Header
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(10, 10, 10, 0)
        
        self.btn_toggle_sidebar = ToolButton(FluentIcon.MENU, self)
        self.btn_toggle_sidebar.setToolTip("Toggle Sidebar")
        self.btn_toggle_sidebar.clicked.connect(self.toggleSidebarRequested.emit)
        
        self.header_layout.addWidget(self.btn_toggle_sidebar)
        self.header_layout.addStretch()
        self.layout.addLayout(self.header_layout)
        
        # 2. Message Area
        self.chat_area = ChatMessageArea(self)
        self.layout.addWidget(self.chat_area)

    def add_user_message(self, text: str, image_paths: Optional[list[str]] = None):
        self.chat_area.add_user_message(text, image_paths)

    def add_ai_message(self, text: str, image_paths: Optional[list[str]] = None):
        self.chat_area.add_ai_message(text, image_paths)

    def show_typing_indicator(self, visible: bool):
        self.chat_area.show_typing_indicator(visible)

    def clear(self):
        self.chat_area.clear()

    def scroll_to_bottom(self):
        self.chat_area.scroll_to_bottom()
