from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import Signal, Qt
from ui.styles import Styles
from ui.widgets.stateful_widget import StatefulWidget
import os

class PathSelectorWidget(StatefulWidget):
    """
    A widget acting as a file or directory selector with a text field and browse button.
    
    Attributes:
        label (str): The label displayed next to the selector.
        select_file (bool): True to select files, False to select directories.
        dialog_title (str): Title of the file dialog.
        path_changed (Signal): Signal emitted when the path changes.
    """
    path_changed = Signal(str)

    def __init__(self, label_text: str, default_path: str = "", select_file: bool = False, dialog_title: str = "Select Path", show_label: bool = True):
        super().__init__()
        self.select_file = select_file
        self.dialog_title = dialog_title
        self.default_path = default_path
        
        # Drag & Drop Support
        self.setAcceptDrops(True)
        
        self._setup_ui(label_text, default_path, show_label)

    def _setup_ui(self, label_text, default_path, show_label):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Label
        if show_label:
            self.lbl_title = QLabel(label_text)
            self.lbl_title.setStyleSheet("font-weight: bold; color: #E0E0E0;")
            layout.addWidget(self.lbl_title)

        # HBox for Input + Button
        h_layout = QHBoxLayout()
        h_layout.setSpacing(8)

        # Input Field
        self.line_edit = QLineEdit(default_path)
        self.line_edit.setStyleSheet(Styles.INPUT_FIELD)
        self.line_edit.setPlaceholderText("Paste path or drag & drop folder here...")
        self.line_edit.textChanged.connect(self._emit_change)
        h_layout.addWidget(self.line_edit)

        # Browse Button
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setStyleSheet(Styles.BTN_GHOST)
        self.btn_browse.setFixedWidth(90)
        self.btn_browse.clicked.connect(self._browse)
        h_layout.addWidget(self.btn_browse)

        layout.addLayout(h_layout)

    def _browse(self):
        current_path = self.line_edit.text()
        start_dir = current_path if os.path.exists(current_path) else ""

        if self.select_file:
            path, _ = QFileDialog.getOpenFileName(self, self.dialog_title, dir=start_dir)
        else:
            path = QFileDialog.getExistingDirectory(self, self.dialog_title, dir=start_dir)
        
        if path:
            self.line_edit.setText(path)

    def _emit_change(self, text):
        self.path_changed.emit(text)
        self.modified.emit()  # Emit modified signal for auto-save
    
    # --- StatefulWidget Protocol ---
    def get_state(self) -> str:
        """Returns the current path as state"""
        return self.get_path()
    
    def set_state(self, value: str):
        """Sets the path from state"""
        self.set_path(value)
    
    def get_default_state(self) -> str:
        """Returns the default path"""
        return self.default_path

    def get_path(self):
        return self.line_edit.text().strip()

    def set_path(self, path):
        self.line_edit.setText(path)

    # --- Drag & Drop Events ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.line_edit.setStyleSheet(Styles.INPUT_FIELD + "border: 1px solid #0078d4;") # Highlight

    def dragLeaveEvent(self, event):
        self.line_edit.setStyleSheet(Styles.INPUT_FIELD) # Reset

    def dropEvent(self, event):
        self.line_edit.setStyleSheet(Styles.INPUT_FIELD) # Reset
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if self.select_file and os.path.isdir(path):
                return # Don't accept folder if looking for file
            self.line_edit.setText(path)
