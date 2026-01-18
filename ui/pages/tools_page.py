from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
from ui.components import NPBasePage
from ui.widgets.tools import ValidatorWidget, ResizerWidget

class ToolsPage(NPBasePage):
    """
    Modern Tools Page.
    Refactored to inherit from NPBasePage.
    Hosts Image Grid Validator and Batch Image Resizer.
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ToolsPage")
        self._setup_ui()

    def _setup_ui(self):
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
        
        # Standardized scroll area from NPBasePage
        self.addScrollArea(container)
