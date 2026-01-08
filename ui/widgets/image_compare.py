from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtCore import Qt
from ui.styles import Colors

class ResizingLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"border: 2px dashed {Colors.BORDER}; color: {Colors.TEXT_MUTED};")
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(self.scaledPixmap())

    def resizeEvent(self, event: QResizeEvent):
        if self._pixmap:
            super().setPixmap(self.scaledPixmap())
        super().resizeEvent(event)

    def scaledPixmap(self):
        if not self._pixmap: return QPixmap()
        return self._pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

class ImageCompareWidget(QWidget):
    """
    Displays an Input Image and an Output Image side-by-side with an arrow.
    """
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_input = ResizingLabel("Waiting Input...")
        self.lbl_output = ResizingLabel("Waiting Output...")
        
        lbl_arrow = QLabel("➡")
        lbl_arrow.setAlignment(Qt.AlignCenter)
        lbl_arrow.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {Colors.TEXT_MUTED};")
        lbl_arrow.setFixedWidth(40)
        
        layout.addWidget(self.lbl_input, 1)
        layout.addWidget(lbl_arrow, 0)
        layout.addWidget(self.lbl_output, 1)

    def set_input(self, path):
        if path:
            self.lbl_input.setPixmap(QPixmap(path))
        else:
            self.lbl_input.setText("Waiting Input...")
            self.lbl_input._pixmap = None

    def set_output(self, path):
        if path:
            self.lbl_output.setPixmap(QPixmap(path))
        else:
            self.lbl_output.setText("Waiting Output...")
            self.lbl_output._pixmap = None

    def clear(self):
        self.lbl_input.setText("Processing...")
        self.lbl_input._pixmap = None
        self.lbl_output.setText("Waiting...")
        self.lbl_output._pixmap = None
