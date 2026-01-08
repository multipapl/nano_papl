from PySide6.QtWidgets import QTextEdit
from ui.styles import Styles

class ConsoleLogWidget(QTextEdit):
    """
    A read-only console log widget with dark background and monospace font.
    """
    def __init__(self, initial_text=""):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet(Styles.TEXT_AREA_CONSOLE)
        if initial_text:
            self.setText(initial_text)

    def append_log(self, message):
        """Appends a new line to the log."""
        self.append(message)
    
    def clear_log(self):
        """Clears the log."""
        self.clear()
