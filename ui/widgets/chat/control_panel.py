from typing import Optional, List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import TransparentPushButton, FluentIcon

from ui.components import AttachmentTrayItem, UIConfig
from ui.widgets.chat import ChatInputArea
from ui.widgets.drag_drop_overlay import DragDropOverlay

class ChatControlPanel(QWidget):
    """
    Modular component for chat inputs, attachments, and drag-and-drop.
    """
    sendClicked = Signal(str, dict)
    attachmentAdded = Signal(list)
    clearClicked = Signal()
    folderClicked = Signal()
    settingChanged = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.current_image_paths = []
        self._init_ui()
        
    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 1. Separator
        self.input_separator = QFrame(self)
        self.input_separator.setFrameShape(QFrame.HLine)
        self.input_separator.setFixedHeight(1)
        self.input_separator.setStyleSheet(f"background-color: {UIConfig.BORDER_SUBTLE_DARK}; border: none;")
        self.layout.addWidget(self.input_separator)
        
        # 2. Attachment Tray
        self.tray_frame = QWidget()
        self.tray_layout = QHBoxLayout(self.tray_frame)
        self.tray_layout.setContentsMargins(20, 8, 20, 8)
        self.tray_layout.setSpacing(8)
        self.tray_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.tray_frame.setVisible(False)
        self.layout.addWidget(self.tray_frame)
        
        # 3. Input Area
        self.input_container = QWidget()
        input_container_layout = QVBoxLayout(self.input_container)
        input_container_layout.setContentsMargins(20, 0, 20, 20)
        
        self.input_area = ChatInputArea(self)
        self.input_area.sendClicked.connect(self._handle_send)
        self.input_area.attachmentAdded.connect(self._handle_attachment_btn)
        self.input_area.clearClicked.connect(self.clearClicked.emit)
        self.input_area.folderClicked.connect(self.folderClicked.emit)
        self.input_area.settingChanged.connect(self.settingChanged.emit)
        
        input_container_layout.addWidget(self.input_area)
        self.layout.addWidget(self.input_container)

    def set_overlay_parent(self, overlay_parent: QWidget):
        # Add drag-and-drop overlay
        self.drag_overlay = DragDropOverlay(overlay_parent)
        self.drag_overlay.filesDropped.connect(self.handle_dropped_files)

    def _handle_send(self, text: str, config: dict):
        self.sendClicked.emit(text, config)

    def _handle_attachment_btn(self):
        from PySide6.QtWidgets import QFileDialog
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if paths:
            self.handle_dropped_files(paths)

    def handle_dropped_files(self, paths: List[str]):
        if paths:
            self.current_image_paths.extend(paths)
            self.update_tray()
            self.attachmentAdded.emit(paths)

    def update_tray(self):
        while self.tray_layout.count():
            item = self.tray_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.current_image_paths:
            self.tray_frame.setVisible(False)
            return
        
        self.tray_frame.setVisible(True)
        for path in self.current_image_paths:
            item = AttachmentTrayItem(path, self)
            item.removed.connect(self.remove_attachment)
            self.tray_layout.addWidget(item)
        self.tray_layout.addStretch()

    def remove_attachment(self, path: str):
        if path in self.current_image_paths:
            self.current_image_paths.remove(path)
            self.update_tray()

    def clear_attachments(self):
        self.current_image_paths = []
        self.update_tray()

    def get_current_images(self) -> List[str]:
        return self.current_image_paths

    def set_enabled(self, enabled: bool):
        self.input_area.set_enabled(enabled)

    def clear_input(self):
        self.input_area.clear_input()
        self.clear_attachments()

    def set_chat_config(self, settings: dict):
        self.input_area.set_chat_config(settings)

    def get_chat_config(self) -> dict:
        return self.input_area.get_chat_config()

    def update_theme_style(self, dark: bool):
        line_color = UIConfig.BORDER_SUBTLE_DARK if dark else UIConfig.BORDER_SUBTLE_LIGHT
        self.input_separator.setStyleSheet(f"background-color: {line_color}; border: none;")
        # ChatInputArea handles its own theme
