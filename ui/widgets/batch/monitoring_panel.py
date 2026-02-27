from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    PushButton, PrimaryPushButton, ProgressBar, 
    CaptionLabel, FluentIcon, TextEdit
)
from ui.components import SectionCard
from .preview import ModernImageCompare

class MonitoringPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._init_ui()
        
    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 30, 20)
        self.layout.setSpacing(15)
        
        # 1. Monitor Card
        self.monitor_card = SectionCard("Live Monitoring")
        self.img_compare = ModernImageCompare()
        self.monitor_card.addWidget(self.img_compare, 1) # stretch 1
        
        self.monitor_card.addWidget(CaptionLabel("Current Prompt"))
        self.txt_prompt = TextEdit()
        self.txt_prompt.setReadOnly(True)
        self.txt_prompt.setFixedHeight(80)
        self.txt_prompt.setPlaceholderText("Generation hasn't started...")
        self.txt_prompt.setToolTip("Full text of the prompt currently being processed by the AI.")
        self.monitor_card.addWidget(self.txt_prompt)
        self.layout.addWidget(self.monitor_card, 7) # Increased stretch factor
        
        # 2. Console & Controls Card
        status_card = SectionCard("Status & Controls")
        
        self.log_area = TextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(120)
        self.log_area.setStyleSheet("font-family: 'Consolas', 'Monaco', monospace; font-size: 11px;")
        self.log_area.setToolTip("Execution log showing technical details, errors, and status updates.")
        status_card.addWidget(self.log_area)
        
        prog_layout = QHBoxLayout()
        self.progress = ProgressBar()
        self.progress.setToolTip("Overall batch completion progress.")
        self.lbl_eta = CaptionLabel("ETA: --:--")
        prog_layout.addWidget(self.progress, 1)
        prog_layout.addWidget(self.lbl_eta)
        status_card.addLayout(prog_layout)
        
        btn_layout = QHBoxLayout()
        self.btn_start = PrimaryPushButton(FluentIcon.PLAY, "START BATCH")
        self.btn_start.setMinimumHeight(45)
        self.btn_start.setToolTip("Start the batch generation process for all images in the input folder.")
        
        self.btn_stop = PushButton(FluentIcon.CLOSE, "STOP")
        self.btn_stop.setMinimumHeight(45)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setToolTip("Interrupt the current batch process.")
        
        btn_layout.addWidget(self.btn_start, 2)
        btn_layout.addWidget(self.btn_stop, 1)
        status_card.addLayout(btn_layout)
        
        self.layout.addWidget(status_card, 0)

    def set_busy(self, busy: bool):
        self.btn_start.setEnabled(not busy)
        self.btn_stop.setEnabled(busy)
        if busy:
            self.progress.setValue(0)
            self.lbl_eta.setText("ETA: Calculating...")
            self.img_compare.clear()
            self.txt_prompt.clear()
            self.log_area.clear()

    def update_preview(self, in_p, out_p, prompt):
        self.txt_prompt.setPlainText(prompt)
        self.img_compare.set_input(in_p)
        self.img_compare.set_output(out_p)

    def append_log(self, text):
        self.log_area.append(text)
        print(f"[BatchLog] {text}")
