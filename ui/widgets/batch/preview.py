
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QFrame
from PySide6.QtGui import QPixmap, QResizeEvent, QPainter, QColor
from PySide6.QtCore import Qt, QSize
from qfluentwidgets import BodyLabel, CaptionLabel, CardWidget, isDarkTheme
from ui.components import UIConfig

class ResizingLabel(QLabel):
    def __init__(self, placeholder="Waiting...", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.placeholder = placeholder
        self.setText(placeholder)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._pixmap = None
        self.current_path = None
        self.setCursor(Qt.PointingHandCursor)
        dark = isDarkTheme()
        secondary = UIConfig.TEXT_SECONDARY_DARK if dark else UIConfig.TEXT_SECONDARY_LIGHT
        self.setToolTip("Click to open image in system viewer")
        self.setStyleSheet(f"color: {secondary}; font-style: italic;")

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        if not pixmap or pixmap.isNull():
            self.setText(self.placeholder)
        else:
            super().setPixmap(self.scaledPixmap())

    def resizeEvent(self, event: QResizeEvent):
        if self._pixmap and not self._pixmap.isNull():
            super().setPixmap(self.scaledPixmap())
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_path:
            if os.path.exists(self.current_path):
                os.startfile(self.current_path)
        super().mousePressEvent(event)

    def scaledPixmap(self):
        if not self._pixmap or self._pixmap.isNull():
            return QPixmap()
        return self._pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

class ModernImageCompare(CardWidget):
    """
    Modern side-by-side image comparison widget with titles and status.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Titles Row
        titles_layout = QHBoxLayout()
        self.lbl_in_title = BodyLabel("INPUT")
        self.lbl_in_title.setAlignment(Qt.AlignCenter)
        self.lbl_out_title = BodyLabel("OUTPUT")
        self.lbl_out_title.setAlignment(Qt.AlignCenter)
        
        titles_layout.addWidget(self.lbl_in_title, 1)
        titles_layout.addSpacing(40) # Space for arrow
        titles_layout.addWidget(self.lbl_out_title, 1)
        layout.addLayout(titles_layout)

        # Images Container
        images_layout = QHBoxLayout()
        images_layout.setSpacing(10)

        # Input Wrapper
        in_frame = QFrame()
        dark = isDarkTheme()
        bg = UIConfig.CARD_BG_DARK if dark else UIConfig.CARD_BG_LIGHT
        in_frame.setStyleSheet(f"background: {bg}; border-radius: 8px;")
        l_in = QVBoxLayout(in_frame)
        l_in.setContentsMargins(5, 5, 5, 5)
        self.lbl_input = ResizingLabel("Input Image")
        l_in.addWidget(self.lbl_input)
        
        # Arrow
        self.lbl_arrow = QLabel("➡")
        self.lbl_arrow.setAlignment(Qt.AlignCenter)
        secondary = UIConfig.TEXT_SECONDARY_DARK if dark else UIConfig.TEXT_SECONDARY_LIGHT
        self.lbl_arrow.setStyleSheet(f"font-size: 24px; color: {secondary};")
        self.lbl_arrow.setFixedWidth(30)

        # Output Wrapper
        out_frame = QFrame()
        out_frame.setStyleSheet(f"background: {bg}; border-radius: 8px;")
        l_out = QVBoxLayout(out_frame)
        l_out.setContentsMargins(5, 5, 5, 5)
        self.lbl_output = ResizingLabel("Generated Output")
        l_out.addWidget(self.lbl_output)

        images_layout.addWidget(in_frame, 1)
        images_layout.addWidget(self.lbl_arrow, 0)
        images_layout.addWidget(out_frame, 1)
        
        layout.addLayout(images_layout, 1)

    def set_input(self, path):
        self.lbl_input.current_path = path
        if path and os.path.exists(path):
            self.lbl_input.setPixmap(QPixmap(path))
        else:
            self.lbl_input.setPixmap(None)

    def set_output(self, path):
        self.lbl_output.current_path = path
        if path and os.path.exists(path):
            self.lbl_output.setPixmap(QPixmap(path))
        else:
            self.lbl_output.setPixmap(None)

    def clear(self):
        self.lbl_input.current_path = None
        self.lbl_output.current_path = None
        self.lbl_input.setPixmap(None)
        self.lbl_output.setPixmap(None)
        self.lbl_input.setText("Processing...")
        self.lbl_output.setText("Waiting...")
