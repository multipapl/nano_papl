from typing import Optional, Union, List, Dict
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QRunnable, QThreadPool, QObject
from PySide6.QtGui import QPainter, QColor, QPaintEvent, QFont, QTextOption, QPixmap
from qfluentwidgets import (
    isDarkTheme, qconfig, PushButton, PrimaryPushButton, FluentIcon, 
    LineEdit, TextEdit, Theme, themeColor, ImageLabel, IconWidget,
    MessageBox, TransparentPushButton, StrongBodyLabel, CardWidget,
    ColorPickerButton, SettingCard, setTheme, setThemeColor, ToolButton,
    ComboBox, CaptionLabel
)
import os
from core.utils import config_helper, image_utils
from core.config.resolutions import SUPPORTED_ASPECT_RATIOS
from core import constants

def init_theme():
    """
    Initialize global application theme settings.
    - Sets theme from config or defaults to Dark.
    - Applies unified accent color.
    """
    # Force dark for now as per previous logic, or load from config if we add it later
    setTheme(Theme.DARK)
    
    dark = isDarkTheme()
    # Use the same logic as in MessageBubble but for global initialization
    default_color = "#4cc2ff" # Sky blue
    saved_color = config_helper.get_value("theme_color", 
                                          config_helper.get_value("theme_color_dark" if dark else "theme_color_light", 
                                                                 default_color))
    setThemeColor(saved_color)

# --- Native Theme-Aware Backgrounds ---

class ThemeAwareBackground(QWidget):
    """
    Native theme-aware background widget using paintEvent.
    Follows QFluentWidgets best practices - no CSS hardcoding.
    
    Reusable for any interface panel (Chat, Tools, Batch, etc.)
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # Fluent Design colors from tokens
        self.light_bg = QColor(UIConfig.CONTAINER_BG_LIGHT)
        self.dark_bg = QColor(UIConfig.CONTAINER_BG_DARK)
        qconfig.themeChanged.connect(self.update)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        # Re-fetch for safety or use cached QColors
        dark = isDarkTheme()
        color = QColor(UIConfig.CONTAINER_BG_DARK if dark else UIConfig.CONTAINER_BG_LIGHT)
        painter.setBrush(color)
        painter.drawRect(self.rect())

# --- centralized configuration ---
class UIConfig:
    """Design Tokens"""
    BUBBLE_RADIUS = 15
    PADDING_STD = 12
    FONT_SIZE_MSG = 9
    AVATAR_SIZE = 20
    MAX_CHAT_IMAGE_WIDTH = 400
    
    # Color Tokens (Semantics) - Official Windows 11 / Fluent Palette
    AI_BUBBLE_BG_DARK = "#2d2d2d"
    AI_BUBBLE_BG_LIGHT = "#f5f5f5"
    
    ACCENT_DEFAULT_DARK = "#4cc2ff"
    ACCENT_DEFAULT_LIGHT = "#0078d4"
    
    # Generic Containers (Fluent Layer 0)
    CONTAINER_BG_DARK = "#202020"    # Official Deep Dark
    CONTAINER_BG_LIGHT = "#f3f3f3"   # Official Subtle Light
    
    # Cards / Surfaces (Fluent Layer 1)
    CARD_BG_DARK = "rgba(255, 255, 255, 0.04)"
    CARD_BG_LIGHT = "rgba(255, 255, 255, 0.7)"
    
    BORDER_SUBTLE_DARK = "rgba(255, 255, 255, 0.08)"
    BORDER_SUBTLE_LIGHT = "rgba(0, 0, 0, 0.06)"
    
    BORDER_HOVER_DARK = "rgba(255, 255, 255, 0.2)"
    BORDER_HOVER_LIGHT = "rgba(0, 0, 0, 0.2)"
    
    # Interactive Overlays
    OVERLAY_HOVER_DARK = "rgba(255, 255, 255, 0.1)"
    OVERLAY_HOVER_LIGHT = "rgba(0, 0, 0, 0.1)"
    OVERLAY_PRESSED_DARK = "rgba(255, 255, 255, 0.2)"
    OVERLAY_PRESSED_LIGHT = "rgba(0, 0, 0, 0.2)"
    
    TEXT_SECONDARY_DARK = "rgba(255, 255, 255, 0.6)"
    TEXT_SECONDARY_LIGHT = "rgba(0, 0, 0, 0.6)"
    
    DANGER_COLOR = "#d32f2f"  # Red for removal/error
    DANGER_HOVER = "#f44336"
    
    # Layout Tokens
    LABEL_MIN_WIDTH = 60

# --- Reusable Components (Factory Pattern) ---

def NPButton(
    text: str,
    icon: Optional[FluentIcon] = None,
    parent: Optional[QWidget] = None,
    is_primary: bool = True
) -> PushButton | PrimaryPushButton:
    """
    Factory function for buttons with type safety.
    
    Args:
        text: Button text label
        icon: Optional FluentIcon
        parent: Optional parent widget
        is_primary: True for PrimaryPushButton, False for PushButton
        
    Returns:
        Configured button instance
    """
    if is_primary:
        btn = PrimaryPushButton(text, parent) if icon is None else PrimaryPushButton(icon, text, parent)
    else:
        btn = PushButton(text, parent) if icon is None else PushButton(icon, text, parent)
    btn.setCursor(Qt.PointingHandCursor)
    return btn

class ImageLoadSignals(QObject):
    """Signals for the async image loader."""
    finished = Signal(QPixmap)
    error = Signal(str)

class ImageLoadWorker(QRunnable):
    """Worker to load and scale images in a separate thread."""
    def __init__(self, path: str, target_width: int):
        super().__init__()
        self.path = path
        self.target_width = target_width
        self.signals = ImageLoadSignals()

    def run(self):
        try:
            # Use image_utils to get cached thumbnail or the original
            # This happens in background thread
            display_path = image_utils.get_or_create_thumbnail(self.path, self.target_width)
            
            pixmap = QPixmap(display_path)
            if pixmap.isNull():
                # Fallback to original if thumbnail failed
                pixmap = QPixmap(self.path)
                
            if not pixmap.isNull():
                if pixmap.width() > self.target_width:
                    pixmap = pixmap.scaledToWidth(self.target_width, Qt.SmoothTransformation)
                self.signals.finished.emit(pixmap)
            else:
                self.signals.error.emit(f"Failed to load image: {self.path}")
        except Exception as e:
            self.signals.error.emit(str(e))

class ClickableImageLabel(ImageLabel):
    """
    ImageLabel with async loading and click signals.
    Left Click -> Open in Viewer
    Right Click -> Attach to Chat
    """
    imageOpened = Signal(str)  # Emits path
    imageClickedForAttach = Signal(str)  # Emits path

    def __init__(self, image_path: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.image_path = image_path
        self.setCursor(Qt.PointingHandCursor)
        self.setBorderRadius(8, 8, 8, 8)
        self.setToolTip("Left Click: Open | Right Click: Attach")
        
        # Start async loading
        self._set_placeholder()
        self._start_async_load()

    def _set_placeholder(self):
        """Set a subtle placeholder state while loading"""
        self.setFixedSize(UIConfig.MAX_CHAT_IMAGE_WIDTH, 150) # Fixed placeholder height
        dark = isDarkTheme()
        opacity = "0.2" if dark else "0.1"
        bg = f"rgba(255, 255, 255, {opacity})" if dark else f"rgba(0, 0, 0, {opacity})"
        self.setStyleSheet(f"background-color: {bg}; border: 1px dashed {UIConfig.BORDER_SUBTLE_DARK};")
        self.setText("Loading...")
        self.setAlignment(Qt.AlignCenter)

    def _start_async_load(self):
        worker = ImageLoadWorker(self.image_path, UIConfig.MAX_CHAT_IMAGE_WIDTH)
        worker.signals.finished.connect(self._on_load_finished)
        worker.signals.error.connect(self._on_load_error)
        QThreadPool.globalInstance().start(worker)

    def _on_load_finished(self, pixmap: QPixmap):
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size()) # Adjust to actual scaled size
        self.setStyleSheet("") # Clear placeholder border

    def _on_load_error(self, error: str):
        # Visually indicate error
        self.setText(f"❌ Load Error\n{os.path.basename(self.image_path)}")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: #ff4d4d; border: 1px solid rgba(255, 77, 77, 0.3); border-radius: 8px;")
        print(f"DEBUG: ClickableImageLabel error: {error}")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.imageOpened.emit(self.image_path)
        elif event.button() == Qt.RightButton:
            self.imageClickedForAttach.emit(self.image_path)
        super().mousePressEvent(event)

class GenerationConfigWidget(QWidget):
    """
    Unified widget for image generation parameters:
    Resolution, Aspect Ratio, and Format.
    """
    configChanged = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None, compact: bool = False) -> None:
        super().__init__(parent)
        self.compact = compact
        self.resolutions = ["1K", "2K", "4K"]
        self.ratios = ["Auto"] + SUPPORTED_ASPECT_RATIOS
        self.formats = constants.IMAGE_FORMATS
        
        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6 if self.compact else 10)

        # 1. Resolution
        self.v_res = QVBoxLayout()
        if not self.compact:
            self.v_res.addWidget(CaptionLabel("Resolution"))
        self.cbox_res = ComboBox(self)
        self.cbox_res.addItems(self.resolutions)
        self.cbox_res.setCurrentIndex(1) # Default 2K
        self.cbox_res.setFixedWidth(80 if self.compact else 110)
        self.v_res.addWidget(self.cbox_res)
        self.main_layout.addLayout(self.v_res)

        # 2. Aspect Ratio
        self.v_ratio = QVBoxLayout()
        if not self.compact:
            self.v_ratio.addWidget(CaptionLabel("Aspect Ratio"))
        self.cbox_ratio = ComboBox(self)
        self.cbox_ratio.addItems(self.ratios)
        self.cbox_ratio.setCurrentIndex(0)
        self.cbox_ratio.setFixedWidth(80 if self.compact else 110)
        self.v_ratio.addWidget(self.cbox_ratio)
        self.main_layout.addLayout(self.v_ratio)

        # 3. Format
        self.v_fmt = QVBoxLayout()
        if not self.compact:
            self.v_fmt.addWidget(CaptionLabel("Format"))
        self.cbox_fmt = ComboBox(self)
        self.cbox_fmt.addItems(self.formats)
        self.cbox_fmt.setCurrentIndex(0)
        self.cbox_fmt.setFixedWidth(70 if self.compact else 80)
        self.v_fmt.addWidget(self.cbox_fmt)
        self.main_layout.addLayout(self.v_fmt)

    def _setup_connections(self):
        self.cbox_res.currentIndexChanged.connect(self._on_changed)
        self.cbox_ratio.currentIndexChanged.connect(self._on_changed)
        self.cbox_fmt.currentIndexChanged.connect(self._on_changed)

    def _on_changed(self):
        self.configChanged.emit(self.get_config())

    def get_config(self) -> dict:
        return {
            "res": self.resolutions[self.cbox_res.currentIndex()],
            "res_index": self.cbox_res.currentIndex(),
            "ratio": self.ratios[self.cbox_ratio.currentIndex()],
            "ratio_index": self.cbox_ratio.currentIndex(),
            "format": self.formats[self.cbox_fmt.currentIndex()],
            "format_index": self.cbox_fmt.currentIndex()
        }

    def set_config(self, config: dict):
        if not config: return
        self.blockSignals(True)
        try:
            if "res_index" in config:
                self.cbox_res.setCurrentIndex(config["res_index"])
            if "ratio_index" in config:
                self.cbox_ratio.setCurrentIndex(config["ratio_index"])
            if "format_index" in config:
                self.cbox_fmt.setCurrentIndex(config["format_index"])
        finally:
            self.blockSignals(False)

    def set_enabled(self, enabled: bool):
        self.cbox_res.setEnabled(enabled)
        self.cbox_ratio.setEnabled(enabled)
        self.cbox_fmt.setEnabled(enabled)

    def set_font_size(self, size: int):
        font = self.cbox_res.font()
        font.setPixelSize(size)
        self.cbox_res.setFont(font)
        self.cbox_ratio.setFont(font)
        self.cbox_fmt.setFont(font)

class MessageBubble(QWidget):
    """Standard Message Component (User & AI)"""
    def __init__(
        self, 
        text: str, 
        is_user: bool = False, 
        image_paths: Optional[list[str]] = None,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.is_user = is_user
        self.image_paths = image_paths or []
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # --- Avatar (AI Only) ---
        if not is_user:
            self.avatar = IconWidget(FluentIcon.CHAT, self)
            self.avatar.setFixedSize(UIConfig.AVATAR_SIZE, UIConfig.AVATAR_SIZE)
        else:
            self.avatar = None
        
        # --- Content Container ---
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        
        # --- Images ---
        for path in self.image_paths:
            if not path or not os.path.exists(path):
                continue
            img_label = ClickableImageLabel(path)
            img_label.imageOpened.connect(self.on_image_opened)
            img_label.imageClickedForAttach.connect(self.on_image_clicked_for_attach)
            self.content_layout.addWidget(img_label)
        
        # --- Bubble Text ---
        self.bubble = QLabel(text)
        self.bubble.setWordWrap(True)
        # Fallback to compatible Markdown rendering
        self.bubble.setTextFormat(Qt.MarkdownText)
        self.bubble.setText(text)
        self.bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        bubble_font = self.bubble.font()
        bubble_font.setPointSize(UIConfig.FONT_SIZE_MSG)
        self.bubble.setFont(bubble_font)
        
        if text:
            self.content_layout.addWidget(self.bubble)
        
        # Dynamic Theme Linking
        qconfig.themeChanged.connect(self.update_style)
        self.update_style()
        
        if is_user:
            layout.addStretch()
            layout.addWidget(self.content_container, 0)
        else:
            if self.avatar:
                layout.addWidget(self.avatar, 0, Qt.AlignTop)
            layout.addWidget(self.content_container, 1)
            layout.addStretch()

    def on_image_opened(self, path: str) -> None:
        """Open image in default system viewer"""
        if os.path.exists(path):
            os.startfile(path)

    def on_image_clicked_for_attach(self, path: str) -> None:
        """Find ChatInterface and call handle_dropped_files"""
        # Bubble -> Container -> ChatMessageArea -> right_widget -> ChatInterface
        p = self.parent()
        while p:
            if hasattr(p, "handle_dropped_files"):
                p.handle_dropped_files([path])
                break
            p = p.parent()

    def update_style(self) -> None:
        """Re-apply styles based on current theme"""
        dark = isDarkTheme()
        
        if self.is_user:
            # FIX: Use raw color from config to avoid library distortion/saturation fixes
            default_color = "#4cc2ff"
            raw_color = config_helper.get_value("theme_color", default_color)
            bg_color = raw_color if not dark else QColor(raw_color).darker(115).name()
            text_color = "#000000"  # Black for better contrast on accent backgrounds
            align_sheet = "border-bottom-right-radius: 2px;"
        else:
            # AI Bubble: Distinct solid surface colors
            bg_color = UIConfig.AI_BUBBLE_BG_DARK if dark else UIConfig.AI_BUBBLE_BG_LIGHT
            text_color = "#ffffff" if dark else "#1f1f1f"
            align_sheet = "border-bottom-left-radius: 2px;"
        
        self.bubble.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color}; 
                color: {text_color};
                border-radius: {UIConfig.BUBBLE_RADIUS}px;
                {align_sheet}
                padding: {UIConfig.PADDING_STD}px;
            }}
        """)
        
        if not self.is_user and self.avatar:
            # IconWidget color is usually handled by theme, but we can set it if needed
            pass

class TypingBubble(QWidget):
    """
    Message bubble shown when AI is 'thinking'.
    Simplified version of MessageBubble.
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        # Avatar
        self.avatar = IconWidget(FluentIcon.CHAT, self)
        self.avatar.setFixedSize(UIConfig.AVATAR_SIZE, UIConfig.AVATAR_SIZE)

        # Bubble
        self.bubble = QLabel("Thinking...")
        self.bubble.setWordWrap(True)
        
        # Italic font for thinking state
        font = self.bubble.font()
        font.setPointSize(UIConfig.FONT_SIZE_MSG)
        font.setItalic(True)
        self.bubble.setFont(font)

        # Style
        dark = isDarkTheme()
        bg_color = UIConfig.AI_BUBBLE_BG_DARK if dark else UIConfig.AI_BUBBLE_BG_LIGHT
        text_color = "rgba(255, 255, 255, 0.6)" if dark else "rgba(0, 0, 0, 0.5)"
        
        self.bubble.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color}; 
                color: {text_color};
                border-radius: {UIConfig.BUBBLE_RADIUS}px;
                border-bottom-left-radius: 2px;
                padding: {UIConfig.PADDING_STD}px;
            }}
        """)

        layout.addWidget(self.avatar, 0, Qt.AlignTop)
        layout.addWidget(self.bubble, 0)
        layout.addStretch()

class AttachmentTrayItem(QWidget):
    """
    Component for single attachment preview in the tray.
    Encapsulates preview and removal logic.
    """
    removed = Signal(str)  # Emits path

    def __init__(self, path: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.path = path
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Image preview
        self.lbl = QLabel()
        self.lbl.setFixedSize(60, 60)
        pix = QPixmap(path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl.setPixmap(pix)
        self.lbl.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        dark = isDarkTheme()
        bg = UIConfig.CARD_BG_DARK if dark else UIConfig.CARD_BG_LIGHT
        border = UIConfig.BORDER_SUBTLE_DARK if dark else UIConfig.BORDER_SUBTLE_LIGHT
        self.lbl.setStyleSheet(f"border: 1px solid {border}; border-radius: 6px; background: {bg};")
        layout.addWidget(self.lbl, 0, Qt.AlignCenter)

        # Remove button
        self.btn_remove = PushButton("×")
        self.btn_remove.setFixedSize(60, 18)
        self.btn_remove.setCursor(Qt.PointingHandCursor)
        self.btn_remove.clicked.connect(lambda: self.removed.emit(self.path))
        
        # Style button
        self.btn_remove.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIConfig.DANGER_COLOR};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {UIConfig.DANGER_HOVER}; }}
        """)
        layout.addWidget(self.btn_remove, 0, Qt.AlignCenter)

class ChatTextEdit(TextEdit):
    """Single-line auto-expanding chat input (Ollama-style)"""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        # Height constraints - CLAUDE STYLE
        self.setMinimumHeight(40)  # Start at ~1 line
        self.max_height = 200  # Max expansion
        
        self.setPlaceholderText("Type a message...")
        
        # Enable word wrap
        self.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        
        # Connect to text changes for auto-expansion
        self.textChanged.connect(self._adjust_height)
        
        # Apply transparent styling (Claude-style)
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                font-size: 14px;
                padding: 4px 8px;
            }
        """)
        
        # Set initial height to single line
        self.setFixedHeight(40)
        
    def _adjust_height(self) -> None:
        """Auto-adjust height based on content"""
        doc = self.document()
        doc.setTextWidth(self.viewport().width())
        doc_height = doc.size().height()
        
        # Add margins/padding
        margins = self.contentsMargins()
        total_height = doc_height + margins.top() + margins.bottom() + 10
        
        # Clamp between 40px min and max
        new_height = max(40, min(total_height, self.max_height))
        self.setFixedHeight(int(new_height))
        
    def _update_style(self) -> None:
        """Update styles based on theme - Claude style (removed, styling is now static in __init__)"""

class NPSearchInput(LineEdit):
    """Standard Input for Search"""
    def __init__(self, placeholder: str = "Search...", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(32)
        self.setMaximumHeight(40)
        
        # FIX: Set font via QFont, not CSS
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)
        
        self.setStyleSheet("LineEdit { border-radius: 20px; padding: 0 15px; }")

class InputDialog(MessageBox):
    """
    Custom Input Dialog with Fluent Design.
    Replaces missing InputDialog in some qfluentwidgets versions.
    """
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(title, content, parent)
        
        # Add LineEdit to the view layout
        self.inputLineEdit = LineEdit(self)
        self.inputLineEdit.setPlaceholderText("Enter text...")
        self.inputLineEdit.setClearButtonEnabled(True)
        
        # The textLayout contains title and content labels
        self.textLayout.addWidget(self.inputLineEdit)
        
        # Connect enter key to accept
        self.inputLineEdit.returnPressed.connect(self.accept)
        
        # Auto-focus on show
        QTimer.singleShot(50, self.inputLineEdit.setFocus)

    def text(self) -> str:
        """Returns the current input text."""
        return self.inputLineEdit.text().strip()

class ModernPathSelector(QWidget):
    """
    Modern version of PathSelectorWidget using QFluentWidgets.
    Supports Drag & Drop and follows the design system.
    """
    path_changed = Signal(str)

    def __init__(self, label_text: str, default_path: str = "", select_file: bool = False, dialog_title: str = "Select Path", parent=None):
        super().__init__(parent)
        self.select_file = select_file
        self.dialog_title = dialog_title
        
        self.setAcceptDrops(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        from qfluentwidgets import BodyLabel
        self.lbl_title = BodyLabel(label_text)
        layout.addWidget(self.lbl_title)

        h_layout = QHBoxLayout()
        h_layout.setSpacing(8)

        self.line_edit = LineEdit()
        if default_path:
            self.line_edit.setText(default_path)
        self.line_edit.setPlaceholderText("Paste path or drag & drop here...")
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.textChanged.connect(self.path_changed.emit)
        h_layout.addWidget(self.line_edit)

        self.btn_browse = PushButton("Browse...")
        self.btn_browse.setFixedWidth(90)
        self.btn_browse.clicked.connect(self._browse)
        h_layout.addWidget(self.btn_browse)

        layout.addLayout(h_layout)

    def _browse(self):
        from PySide6.QtWidgets import QFileDialog
        curr = self.line_edit.text()
        start = curr if os.path.exists(curr) else ""

        if self.select_file:
            path, _ = QFileDialog.getOpenFileName(self, self.dialog_title, dir=start)
        else:
            path = QFileDialog.getExistingDirectory(self, self.dialog_title, dir=start)
        
        if path:
            self.line_edit.setText(path)

    def get_path(self) -> str:
        return self.line_edit.text().strip()

    def set_path(self, path: str):
        self.line_edit.setText(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if self.select_file and os.path.isdir(path):
                return
            self.line_edit.setText(path)

class AdaptiveTextEdit(TextEdit):
    """
    TextEdit that adjusts its height based on content, 
    similar to ChatTextEdit but keeping standard card styling.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.textChanged.connect(self._adjust_height)
        self.min_h = 40
        self.max_h = 250
        
        self.setFixedHeight(self.min_h)

    def _adjust_height(self):
        doc = self.document()
        doc.setTextWidth(self.viewport().width())
        h = int(doc.size().height() + 15)
        new_h = max(self.min_h, min(h, self.max_h))
        self.setFixedHeight(new_h)
        
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._adjust_height()

class SectionCard(CardWidget):
    """A card-like container for UI sections using qfluentwidgets CardWidget."""
    def __init__(self, title: str, icon: Optional[FluentIcon] = None, parent=None):
        super().__init__(parent)
        self.setBorderRadius(10)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        if icon:
            self.icon_widget = IconWidget(icon, self)
            self.icon_widget.setFixedSize(16, 16)
            header_layout.addWidget(self.icon_widget)
            
        self.title_label = StrongBodyLabel(title)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        layout.addLayout(self.content_layout, 1)
        
        qconfig.themeChanged.connect(self.update)

    def addWidget(self, widget: QWidget, stretch: int = 0):
        self.content_layout.addWidget(widget, stretch)

    def addLayout(self, layout: QHBoxLayout | QVBoxLayout, stretch: int = 0):
        self.content_layout.addLayout(layout, stretch)

class CustomColorSettingCard(SettingCard):
    """Color setting card that works with raw QColor instead of qconfig."""
    colorChanged = Signal(QColor)

    def __init__(self, color, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.btnReset = ToolButton(FluentIcon.SYNC, self)
        self.btnReset.setFixedSize(30, 30)
        self.btnReset.setToolTip("Reset to Default")
        
        self.colorPicker = ColorPickerButton(color, title, self)
        self.colorPicker.colorChanged.connect(self.colorChanged)
        
        self.hBoxLayout.addWidget(self.btnReset, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.colorPicker, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

def get_scroll_style(dark=None):
    """Returns standardized transparent scroll area stylesheet."""
    if dark is None:
        dark = isDarkTheme()
    
    line_color = UIConfig.BORDER_SUBTLE_DARK if dark else UIConfig.BORDER_SUBTLE_LIGHT
    return f"""
        QScrollArea {{ 
            border: none; 
            background: transparent; 
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {line_color};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """
