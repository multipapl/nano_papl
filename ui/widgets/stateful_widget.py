from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Signal
from ui.styles import Styles
from typing import Any


class StatefulWidget(QWidget):
    """
    Base protocol/mixin for widgets that can save and restore their state.
    All custom widgets should inherit from this to enable automated state management.
    """
    modified = Signal()  # Emitted when the widget's state changes
    
    def get_state(self) -> Any:
        """
        Returns the current state of the widget.
        Can return any JSON-serializable type (str, int, dict, list, etc.)
        
        Override this method in subclasses.
        """
        raise NotImplementedError("Subclass must implement get_state()")
    
    def set_state(self, value: Any):
        """
        Restores the widget's state from the provided value.
        
        Args:
            value: The state to restore (must match the type returned by get_state)
        
        Override this method in subclasses.
        """
        raise NotImplementedError("Subclass must implement set_state()")
    
    def get_default_state(self) -> Any:
        """
        Returns the default state for this widget (used for reset functionality).
        
        Override this method in subclasses if different from empty/zero values.
        """
        return None


class SettingRowWidget(StatefulWidget):
    """
    A reusable widget combining an input field with a reset button.
    Implements the StatefulWidget protocol for automated state management.
    
    This replaces the repetitive 'create_setting_row_new' pattern.
    """
    
    def __init__(self, default_value: str = "", reset_value: str = None, placeholder: str = ""):
        super().__init__()
        self.default_value = default_value
        self.reset_value = reset_value if reset_value is not None else default_value
        
        self._setup_ui(placeholder)
    
    def _setup_ui(self, placeholder):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Input Field
        self.line_edit = QLineEdit(self.default_value)
        self.line_edit.setStyleSheet(Styles.INPUT_FIELD)
        if placeholder:
            self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.line_edit)
        
        # Reset Button
        self.btn_reset = QPushButton("R")
        self.btn_reset.setFixedWidth(25)
        self.btn_reset.setStyleSheet(Styles.BTN_GHOST)
        self.btn_reset.clicked.connect(self.reset)
        layout.addWidget(self.btn_reset)
    
    def _on_text_changed(self, text):
        """Emit modified signal when text changes"""
        self.modified.emit()
    
    def get_state(self) -> str:
        """Returns the current text value"""
        return self.line_edit.text()
    
    def set_state(self, value: str):
        """Sets the text value without emitting modified signal"""
        self.line_edit.blockSignals(True)
        self.line_edit.setText(value)
        self.line_edit.blockSignals(False)
    
    def get_default_state(self) -> str:
        """Returns the default/reset value"""
        return self.reset_value
    
    def reset(self):
        """Reset to default value"""
        self.set_state(self.reset_value)
        self.modified.emit()
    
    def text(self) -> str:
        """Convenience method for compatibility with QLineEdit"""
        return self.get_state()
    
    def setText(self, text: str):
        """Convenience method for compatibility with QLineEdit"""
        self.set_state(text)
