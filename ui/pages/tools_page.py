from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from ui.components import ThemeAwareBackground
from ui.widgets.tools import ValidatorWidget, ResizerWidget

class ToolsPage(ThemeAwareBackground):
    """
    Modern Tools Page.
    Hosts Image Grid Validator and Batch Image Resizer.
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ToolsPage")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        from ui.components import get_scroll_style
        scroll.setStyleSheet(get_scroll_style())
        scroll.viewport().setStyleSheet("background: transparent;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)

        # 1. Validator
        self.validator = ValidatorWidget(self)
        scroll_layout.addWidget(self.validator)

        # 2. Resizer
        self.resizer = ResizerWidget(self)
        scroll_layout.addWidget(self.resizer)

        scroll_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
