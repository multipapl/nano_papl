from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    LineEdit, BodyLabel, ProgressBar, TextEdit, 
    PrimaryPushButton, FluentIcon
)
from ui.components import SectionCard, ModernPathSelector, NPButton
from core.workers.resizer_worker import ResizerWorker

class ResizerWidget(QWidget):
    """
    Batch Image Resizer component for the Tools page.
    Handles multi-threaded image resizing with progress tracking.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resizer_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        self.card = SectionCard("Batch Image Resizer", FluentIcon.PHOTO)
        
        # Paths
        self.input_path = ModernPathSelector("Input Folder:", select_file=False)
        self.input_path.setToolTip("Folder containing images to resize.")
        self.card.addWidget(self.input_path)
        
        self.output_path = ModernPathSelector("Output Folder:", select_file=False)
        self.output_path.setToolTip("Destination folder for resized images.")
        self.card.addWidget(self.output_path)
        
        # Resolution
        # We'll use a horizontal layout for width/height
        h_res = QHBoxLayout()
        h_res.setSpacing(10)
        
        self.res_width = LineEdit()
        self.res_width.setPlaceholderText("Width (px)")
        self.res_width.setText("1920")
        self.res_width.setClearButtonEnabled(True)
        self.res_width.setToolTip("Target width in pixels.")
        h_res.addWidget(BodyLabel("Width:"))
        h_res.addWidget(self.res_width)
        
        self.res_height = LineEdit()
        self.res_height.setPlaceholderText("Height (px)")
        self.res_height.setText("1080")
        self.res_height.setClearButtonEnabled(True)
        self.res_height.setToolTip("Target height in pixels.")
        h_res.addWidget(BodyLabel("Height:"))
        h_res.addWidget(self.res_height)
        
        self.card.addLayout(h_res)
        
        # Progress
        self.progress = ProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)
        self.card.addWidget(self.progress)
        
        # Start Button
        self.btn_start = NPButton("START RESIZING", FluentIcon.PLAY)
        self.btn_start.clicked.connect(self.start_resizing)
        self.btn_start.setToolTip("Begin the batch resizing process.")
        self.card.addWidget(self.btn_start)
        
        # Log Area
        self.resizer_log = TextEdit()
        self.resizer_log.setReadOnly(True)
        self.resizer_log.setFixedHeight(100)
        self.resizer_log.setPlaceholderText("Select folders and resolution, then click Start Resizing...")
        self.resizer_log.setToolTip("Status of the resizing task and any errors encountered.")
        self.card.addWidget(self.resizer_log)
        
        layout.addWidget(self.card)

    def start_resizing(self):
        input_folder = self.input_path.get_path()
        output_folder = self.output_path.get_path()
        width_str = self.res_width.text().strip()
        height_str = self.res_height.text().strip()
        
        if not input_folder or not Path(input_folder).exists():
            QMessageBox.warning(self, "Error", "Input folder does not exist!")
            return
        
        if not output_folder:
            QMessageBox.warning(self, "Error", "Output folder cannot be empty!")
            return
            
        try:
            target_width = int(width_str)
            target_height = int(height_str)
            if target_width <= 0 or target_height <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid Width/Height!")
            return
            
        self.resizer_log.clear()
        self.resizer_log.append(f"🎯 Target: {target_width}x{target_height}")
        self.resizer_log.append(f"📂 Input: {input_folder}")
        self.resizer_log.append(f"📁 Output: {output_folder}\n")
        
        self.btn_start.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        self.resizer_worker = ResizerWorker(
            input_folder, output_folder, target_width, target_height
        )
        self.resizer_worker.progress.connect(self.on_progress)
        self.resizer_worker.finished.connect(self.on_finished)
        self.resizer_worker.log_message.connect(self.on_log)
        self.resizer_worker.start()

    def on_progress(self, current: int, total: int):
        self.progress.setMaximum(total)
        self.progress.setValue(current)
        # ProgressBar in FluentWidgets uses different format if needed, but simple is fine
    
    def on_log(self, message: str):
        self.resizer_log.append(message)
    
    def on_finished(self, success: bool, message: str):
        self.btn_start.setEnabled(True)
        self.progress.setVisible(False)
        
        if success:
            self.resizer_log.append(f"\n✅ {message}")
            QMessageBox.information(self, "Complete", message)
        else:
            self.resizer_log.append(f"\n❌ {message}")
            QMessageBox.critical(self, "Error", message)

        if self.resizer_worker:
            self.resizer_worker.deleteLater()
            self.resizer_worker = None
