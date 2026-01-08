from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from ui.styles import Styles

class ActionHeaderWidget(QWidget):
    """
    A standardized section header with an optional action button (e.g. Reset).
    """
    def __init__(self, title: str, on_reset=None, reset_text="Reset"):
        super().__init__()
        self.init_ui(title, on_reset, reset_text)

    def init_ui(self, title, on_reset, reset_text):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5) # Slight top/bottom margin
        
        # Title
        lbl = QLabel(title)
        lbl.setStyleSheet(Styles.SECTION_HEADER)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(lbl)

        # Optional Action Button
        if on_reset:
            btn_reset = QPushButton(reset_text)
            btn_reset.setStyleSheet(Styles.BTN_GHOST)
            btn_reset.setFixedHeight(24) 
            btn_reset.clicked.connect(on_reset)
            layout.addWidget(btn_reset)
