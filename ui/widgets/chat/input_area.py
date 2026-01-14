from typing import Optional, Dict
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QToolButton
from PySide6.QtCore import Qt, QSize, Signal, QEvent, QPoint
from PySide6.QtGui import QAction, QFont

from qfluentwidgets import (
    FluentIcon, ToolButton, PushButton, TransparentPushButton, RoundMenu, Action, 
    isDarkTheme, qconfig, themeColor, TransparentDropDownPushButton, CheckBox,
    ComboBox
)

from ui.components import ChatTextEdit
from core.utils import config_helper

class ChatInputArea(QFrame):
    """
    Standalone Chat Input Component.
    Encapsulates: Input Box, Toolbar, Menus, Styling.
    """
    
    # Signals
    sendClicked = Signal(str, dict)  # Emits (text, config_dict)
    attachmentAdded = Signal()       # Emits when attach button clicked
    clearClicked = Signal()          # Emits when clear button clicked
    folderClicked = Signal()         # Emits when folder button clicked
    settingChanged = Signal(dict)    # Emits full config dict when any setting changes
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ChatInputContainer")
        
        self.current_model = 0 
        self.models = ["gemini-3-pro-image-preview", "gemini-3-flash-preview"]
        self.model_labels = ["Pro", "Flash"]
        
        self.current_ratio = 0
        self.ratios = ["1:1", "16:9", "4:3", "9:16", "3:4"]
        
        self.current_res = 1  # Default 2K
        self.resolutions = ["1K", "2K", "4K"]

        self._init_ui()
        self._setup_connections()
        
        # Initial Theme Apply
        self._on_theme_changed()

    def _create_combobox(self, items: list, icons: list = None) -> ComboBox:
        """Helper to create a styled ComboBox"""
        cbox = ComboBox(self)
        if icons:
            for i, (text, icon) in enumerate(zip(items, icons)):
                cbox.addItem(text, icon)
        else:
            cbox.addItems(items)
            
        cbox.setObjectName("StealthComboBox")
        cbox.setFocusPolicy(Qt.NoFocus)
        return cbox

    def _create_stealth_button(self, text: str, tooltip: str, icon: FluentIcon) -> TransparentPushButton:
        """Helper to create a styled stealth button (Chip Style) - For simple toggles"""
        btn = TransparentPushButton(text, self, icon)
        btn.setToolTip(tooltip)
        btn.setObjectName("StealthButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.NoFocus)
        
        # Guide Compliance: Set font size via code
        font = btn.font()
        font.setPixelSize(12)
        font.setWeight(QFont.Medium)
        btn.setFont(font)
        
        return btn

    def _init_ui(self):
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(8, 6, 8, 6)
        container_layout.setSpacing(4)
        
        # --- TOP ROW: Message Input ---
        message_row = QWidget()
        message_layout = QHBoxLayout(message_row)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(8)
        
        # Attach Button
        self.btn_attach = ToolButton(FluentIcon.ADD, self)
        self.btn_attach.setFixedSize(28, 28)
        self.btn_attach.setIconSize(QSize(14, 14))
        self.btn_attach.setToolTip("Attach Images")
        self.btn_attach.clicked.connect(self.attachmentAdded.emit)
        message_layout.addWidget(self.btn_attach)
        
        # Input Box
        self.input_box = ChatTextEdit()
        self.input_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_box.installEventFilter(self)
        message_layout.addWidget(self.input_box, 1)
        
        # Send Button
        self.btn_send = ToolButton(FluentIcon.SEND, self)
        self.btn_send.setFixedSize(28, 28)
        self.btn_send.setIconSize(QSize(14, 14))
        self.btn_send.setToolTip("Send Message (Ctrl+Enter)")
        self.btn_send.clicked.connect(self._on_send)
        message_layout.addWidget(self.btn_send, 0, Qt.AlignVCenter)
        
        container_layout.addWidget(message_row)
        
        # Generic Separator (Subtle Divider)
        self.separator = QFrame(self)
        self.separator.setObjectName("ChatSeparator")
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.separator.setFixedHeight(1)
        container_layout.addWidget(self.separator)
        
        # --- BOTTOM ROW: Toolbar ---
        toolbar_row = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_row)
        toolbar_layout.setContentsMargins(0, 4, 0, 0) # Added top margin
        toolbar_layout.setSpacing(6)
        
        # Uniform Font (13px as requested)
        font = QFont()
        font.setPixelSize(13)
        
        # Image Mode Toggle (CheckBox)
        self.chk_img_mode = CheckBox("Gen Image", self)
        self.chk_img_mode.setChecked(True)
        self.chk_img_mode.setFont(font)
        self.chk_img_mode.toggled.connect(self._toggle_img_mode)
        toolbar_layout.addWidget(self.chk_img_mode)
        
        # Vertical Separator
        self.v_sep = QFrame(self)
        self.v_sep.setFrameShape(QFrame.VLine)
        self.v_sep.setFrameShadow(QFrame.Sunken)
        self.v_sep.setFixedSize(1, 16) # Height 16px
        toolbar_layout.addWidget(self.v_sep)
        
        # Model Selector (ComboBox)
        self.cbox_model = self._create_combobox(self.model_labels)
        self.cbox_model.setFont(font)
        self.cbox_model.setFixedWidth(110)
        self.cbox_model.setCurrentIndex(0)
        self.cbox_model.setToolTip("Select AI Model")
        toolbar_layout.addWidget(self.cbox_model)
        
        # Ratio Selector (ComboBox)
        self.cbox_ratio = self._create_combobox(self.ratios)
        self.cbox_ratio.setFont(font)
        self.cbox_ratio.setFixedWidth(110)
        self.cbox_ratio.setCurrentIndex(0)
        self.cbox_ratio.setToolTip("Select Image Aspect Ratio")
        toolbar_layout.addWidget(self.cbox_ratio)
        
        # Resolution Selector (ComboBox)
        self.cbox_res = self._create_combobox(self.resolutions)
        self.cbox_res.setFont(font)
        self.cbox_res.setFixedWidth(110)
        self.cbox_res.setCurrentIndex(1) # Default 2K
        self.cbox_res.setToolTip("Select Image Resolution")
        toolbar_layout.addWidget(self.cbox_res)
        
        toolbar_layout.addStretch()
        
        # Clear & Folder Actions
        self.btn_clear = ToolButton(FluentIcon.DELETE, self)
        self.btn_clear.setFixedSize(28, 28)
        self.btn_clear.setIconSize(QSize(14, 14))
        self.btn_clear.setToolTip("Clear current chat history")
        self.btn_clear.clicked.connect(self.clearClicked.emit)
        toolbar_layout.addWidget(self.btn_clear)
        
        self.btn_folder = ToolButton(FluentIcon.FOLDER, self)
        self.btn_folder.setFixedSize(28, 28)
        self.btn_folder.setIconSize(QSize(14, 14))
        self.btn_folder.setToolTip("Open folder with generated images")
        self.btn_folder.clicked.connect(self.folderClicked.emit)
        toolbar_layout.addWidget(self.btn_folder)
        
        container_layout.addWidget(toolbar_row)
        
    def _setup_connections(self):
        qconfig.themeChanged.connect(self._on_theme_changed)
        
        # Settings change tracking
        self.chk_img_mode.toggled.connect(self._emit_settings_changed)
        self.cbox_model.currentIndexChanged.connect(self._emit_settings_changed)
        self.cbox_ratio.currentIndexChanged.connect(self._emit_settings_changed)
        self.cbox_res.currentIndexChanged.connect(self._emit_settings_changed)

    def _emit_settings_changed(self):
        """Emit the current configuration when any setting is manually changed"""
        self.settingChanged.emit(self.get_chat_config())

    def _toggle_img_mode(self, checked: bool):
        self.cbox_ratio.setEnabled(checked)
        self.cbox_res.setEnabled(checked)

    def _on_send(self):
        text = self.input_box.toPlainText().strip()
        self.sendClicked.emit(text, self.get_chat_config())

    def get_chat_config(self) -> dict:
        """Returns current settings state as a dictionary"""
        return {
            "model": self.models[self.cbox_model.currentIndex()],
            "model_index": self.cbox_model.currentIndex(),
            "ratio": self.ratios[self.cbox_ratio.currentIndex()],
            "ratio_index": self.cbox_ratio.currentIndex(),
            "res": self.resolutions[self.cbox_res.currentIndex()],
            "res_index": self.cbox_res.currentIndex(),
            "img_mode": self.chk_img_mode.isChecked()
        }

    def set_chat_config(self, config: dict):
        """Applies a configuration dictionary to the UI elements"""
        if not config: return
        
        # Block signals to prevent infinite recursion or multiple saves
        self.chk_img_mode.blockSignals(True)
        self.cbox_model.blockSignals(True)
        self.cbox_ratio.blockSignals(True)
        self.cbox_res.blockSignals(True)
        
        try:
            if "img_mode" in config:
                self.chk_img_mode.setChecked(config["img_mode"])
                self._toggle_img_mode(config["img_mode"])
                
            if "model_index" in config:
                self.cbox_model.setCurrentIndex(config["model_index"])
            elif "model" in config and config["model"] in self.models:
                self.cbox_model.setCurrentIndex(self.models.index(config["model"]))
                
            if "ratio_index" in config:
                self.cbox_ratio.setCurrentIndex(config["ratio_index"])
            elif "ratio" in config and config["ratio"] in self.ratios:
                self.cbox_ratio.setCurrentIndex(self.ratios.index(config["ratio"]))
                
            if "res_index" in config:
                self.cbox_res.setCurrentIndex(config["res_index"])
            elif "res" in config and config["res"] in self.resolutions:
                self.cbox_res.setCurrentIndex(self.resolutions.index(config["res"]))
        finally:
            self.chk_img_mode.blockSignals(False)
            self.cbox_model.blockSignals(False)
            self.cbox_ratio.blockSignals(False)
            self.cbox_res.blockSignals(False)

    def clear_input(self):
        """Clear text field"""
        self.input_box.clear()

    def set_enabled(self, enabled: bool):
        """Enable/Disable all controls"""
        self.btn_send.setEnabled(enabled)
        self.input_box.setEnabled(enabled)
        self.btn_attach.setEnabled(enabled)

    def eventFilter(self, obj, event):
        if obj == self.input_box and event.type() == QEvent.KeyPress:
            # Change to Ctrl+Enter as requested
            if event.key() == Qt.Key_Return and (event.modifiers() & Qt.ControlModifier):
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    # --- Styling ---
    
    def _on_theme_changed(self):
        self._apply_container_style()
        self._apply_send_button_style()
        self._apply_toolbar_button_styles()
        self._update_toggle_style()

    def _apply_container_style(self):
        dark = isDarkTheme()
        if dark:
            bg = "rgba(43, 43, 43, 1)"
            border = "rgba(255, 255, 255, 0.1)"
            hover_border = "rgba(255, 255, 255, 0.2)"
        else:
            bg = "rgba(255, 255, 255, 1)"
            border = "rgba(0, 0, 0, 0.1)"
            hover_border = "rgba(0, 0, 0, 0.2)"
        
        self.setStyleSheet(f"""
            QFrame#ChatInputContainer {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QFrame#ChatInputContainer:hover {{
                border: 1px solid {hover_border};
            }}
        """)
        
        # Separator Style
        sep_color = "rgba(255, 255, 255, 0.1)" if dark else "rgba(0, 0, 0, 0.08)"
        self.separator.setStyleSheet(f"background-color: {sep_color}; border: none;")
        self.v_sep.setStyleSheet(f"background-color: {sep_color}; border: none;")

    def _apply_toolbar_button_styles(self):
        # Native ComboBox handles its own standard styles.
        pass

    def _apply_send_button_style(self):
        dark = isDarkTheme()
        # FIX: Use raw color from config for perfect fidelity
        primary = config_helper.get_value("theme_color_dark" if dark else "theme_color_light", "#4cc2ff")
        
        # Set icon color explicitly to black as requested by user
        from PySide6.QtGui import QColor
        self.btn_send.setIcon(FluentIcon.SEND.icon(color=QColor(Qt.black)))
        
        if dark:
            hover = "rgba(255, 255, 255, 0.1)"
            pressed = "rgba(255, 255, 255, 0.05)"
        else:
            hover = "rgba(0, 0, 0, 0.1)"
            pressed = "rgba(0, 0, 0, 0.05)"
        
        self.btn_send.setStyleSheet(f"""
            ToolButton {{
                border-radius: 14px;
                background-color: {primary};
                border: none;
            }}
            ToolButton:hover {{
                background-color: {primary};
                border: 1px solid {hover};
            }}
            ToolButton:pressed {{
                background-color: {primary};
                border: 1px solid {pressed};
            }}
        """)



    def _update_toggle_style(self):
        # Native CheckBox styling is usually sufficient. 
        # We handle text color if needed, but qfluentwidgets handles it automatically.
        pass
