
import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QPushButton, QProgressBar, QTextEdit, QFileDialog, 
    QCheckBox, QComboBox, QGroupBox, QSpinBox, QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal

from core.utils import config_helper
from core.services.comfy_orchestrator import ComfyOrchestrator
from ui.styles import Styles, Colors
from ui.base_tab import BaseTab

class ComfyWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(float)
    finished_signal = Signal()
    error_signal = Signal(str)
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.manager = None

    def run(self):
        try:
            self.manager = ComfyOrchestrator(
                self.settings,
                log_callback=self.log_signal.emit,
                progress_callback=self.progress_signal.emit
            )
            self.manager.process_batch()
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()

    def stop(self):
        if self.manager:
            self.manager.stop()
        self.quit()

class TabComfyUI(BaseTab):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.default_workflow_path = "data/api_nano_banana_pro.json"
        
        # Apply Global Shared Styles containing generic widget resets
        self.setStyleSheet(Styles.GLOBAL + Styles.INPUT_FIELD + Styles.SECTION_HEADER + Styles.BTN_BASE)
        
        self._setup_ui()
        self._register_fields()
        self.load_state()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- LEFT PANEL (Controls) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Directories & Config Group
        grp_config = QGroupBox("Configuration")
        layout_config = QGridLayout(grp_config)
        layout_config.setVerticalSpacing(10)
        
        # Paths
        layout_config.addWidget(QLabel("Input:"), 0, 0)
        self.line_input = QLineEdit()
        self.line_input.setPlaceholderText("Folder with images & prompts.md")
        layout_config.addWidget(self.line_input, 0, 1)
        btn_in = QPushButton("Browse")
        btn_in.setStyleSheet(Styles.BTN_GHOST)
        btn_in.clicked.connect(lambda: self._browse_dir(self.line_input))
        layout_config.addWidget(btn_in, 0, 2)
        
        layout_config.addWidget(QLabel("Output:"), 1, 0)
        self.line_output = QLineEdit()
        layout_config.addWidget(self.line_output, 1, 1)
        btn_out = QPushButton("Browse")
        btn_out.setStyleSheet(Styles.BTN_GHOST)
        btn_out.clicked.connect(lambda: self._browse_dir(self.line_output))
        layout_config.addWidget(btn_out, 1, 2)
        
        # Params Line
        hbox_params = QHBoxLayout()
        
        hbox_params.addWidget(QLabel("Res:"))
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1K", "2K", "4K"])
        hbox_params.addWidget(self.combo_res)
        
        hbox_params.addWidget(QLabel("  Ratio:"))
        self.combo_ratio = QComboBox()
        self.combo_ratio.addItems(["1:1", "16:9", "9:16", "4:5", "3:4", "Manual"])
        hbox_params.addWidget(self.combo_ratio)
        
        hbox_params.addStretch()
        layout_config.addLayout(hbox_params, 2, 1, 1, 2)
        
        # Seed Line
        hbox_seed = QHBoxLayout()
        self.check_random_seed = QCheckBox("Random Seed")
        self.check_random_seed.setChecked(True)
        self.check_random_seed.toggled.connect(self._toggle_seed_input)
        
        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 999999999)
        self.spin_seed.setValue(123456789)
        self.spin_seed.setEnabled(False)
        self.spin_seed.setMinimumWidth(120)
        
        hbox_seed.addWidget(self.check_random_seed)
        hbox_seed.addWidget(self.spin_seed)
        hbox_seed.addStretch()
        
        layout_config.addLayout(hbox_seed, 3, 1, 1, 2)
        
        left_layout.addWidget(grp_config)

        # 2. System Prompt Group
        grp_prompt = QGroupBox("System Prompt Override")
        layout_prompt = QVBoxLayout(grp_prompt)
        
        self.text_sys_prompt = QTextEdit()
        self.text_sys_prompt.setPlaceholderText("Optional: Enter text to override workflow default...")
        self.text_sys_prompt.setFixedHeight(100) # Balanced height
        
        # Load default
        default_sys_prompt = ""
        try:
            if os.path.exists(self.default_workflow_path):
                with open(self.default_workflow_path, 'r', encoding='utf-8') as f:
                    wf = json.load(f)
                    if "35" in wf and "inputs" in wf["35"]:
                         default_sys_prompt = wf["35"]["inputs"].get("system_prompt", "")
        except: pass
        self.text_sys_prompt.setText(default_sys_prompt)
        
        layout_prompt.addWidget(self.text_sys_prompt)
        left_layout.addWidget(grp_prompt)
        
        left_layout.addStretch()

        # 3. Actions Area
        hbox_actions = QHBoxLayout()
        
        self.check_dry_run = QCheckBox("Dry Run")
        self.check_dry_run.setToolTip("Uploads resources but does not generate images.")
        self.check_dry_run.setChecked(True)
        self.check_dry_run.setStyleSheet("font-weight: bold; color: #E0E0E0;")
        
        hbox_actions.addWidget(self.check_dry_run)
        
        left_layout.addLayout(hbox_actions)
        
        # Buttons (Unified Style)
        hbox_btns = QHBoxLayout()
        
        self.btn_start = QPushButton("START BATCH")
        self.btn_start.setMinimumHeight(45)
        self.btn_start.setStyleSheet(Styles.BTN_PRIMARY)
        self.btn_start.clicked.connect(self._toggle_process)
        
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setMinimumHeight(45)
        self.btn_stop.setStyleSheet(Styles.BTN_DANGER)
        self.btn_stop.clicked.connect(self._stop_process)
        self.btn_stop.setEnabled(False) # Initially disabled
        
        hbox_btns.addWidget(self.btn_start, stretch=3)
        hbox_btns.addWidget(self.btn_stop, stretch=1)
        
        left_layout.addLayout(hbox_btns)

        # --- RIGHT PANEL (Logs) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        grp_logs = QGroupBox("Process Logs")
        layout_logs = QVBoxLayout(grp_logs)
        layout_logs.setContentsMargins(5, 15, 5, 5) # GroupBox padding adjustment
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        layout_logs.addWidget(self.progress)
        
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setStyleSheet(Styles.TEXT_AREA_CONSOLE)
        self.text_log.setPlaceholderText("Waiting to start...")
        layout_logs.addWidget(self.text_log)
        
        right_layout.addWidget(grp_logs)

        # --- COMBINE WITH SPLITTER ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 4) # 40%
        splitter.setStretchFactor(1, 6) # 60%
        
        main_layout.addWidget(splitter)
    
    def _register_fields(self):
        """Register all stateful widgets with BaseTab"""
        self.register_field("comfy_input", self.line_input)
        self.register_field("comfy_output", self.line_output)
        self.register_field("comfy_sys_prompt", self.text_sys_prompt)
        self.register_field("comfy_resolution", self.combo_res)
        self.register_field("comfy_ratio", self.combo_ratio)
        self.register_field("comfy_random_seed", self.check_random_seed)
        self.register_field("comfy_seed_value", self.spin_seed)
        self.register_field("comfy_dry_run", self.check_dry_run)

    def _browse_dir(self, line_edit):
        d = QFileDialog.getExistingDirectory(self, "Select Directory")
        if d: line_edit.setText(d)
        
    def _toggle_seed_input(self, checked):
        self.spin_seed.setEnabled(not checked)
        if not checked:
            self.spin_seed.setFocus()

    def _log(self, msg):
        self.text_log.append(msg)
        sb = self.text_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _toggle_process(self):
        # Start Logic
        inp = self.line_input.text()
        outp = self.line_output.text()
        
        if not inp or not outp:
            self._log("Error: Please select both Input and Output directories.")
            return
            
        self._save_settings()
        
        # Toggle UI State
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.text_log.clear()
        self.progress.setValue(0)
        
        # Gather settings
        batch_settings = {
            "comfy_url": config_helper.get_value("comfy_url", "http://127.0.0.1:8188"),
            "api_key": config_helper.get_value("comfy_api_key", ""),
            "input_path": inp,
            "output_path": outp,
            "resolution": self.combo_res.currentText(),
            "ratio": self.combo_ratio.currentText(),
            "dry_run": self.check_dry_run.isChecked(),
            "workflow_path": self.default_workflow_path,
            "system_prompt": self.text_sys_prompt.toPlainText(),
            "use_random_seed": self.check_random_seed.isChecked(),
            "seed_value": self.spin_seed.value()
        }
        
        self.worker = ComfyWorker(batch_settings)
        self.worker.log_signal.connect(self._log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _stop_process(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self._log("!!! STOPPED BY USER !!!")
            self._on_finished()

    def _on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._log("--- Cycle Finished ---")

    def _save_settings(self):
        """Simplified - uses BaseTab's automated save"""
        super().save_state()

    def load_state(self):
        """Override to handle sys_prompt from workflow default"""
        super().load_state()
        
        # Load default sys prompt from workflow if not already set
        if not self.text_sys_prompt.toPlainText():
            default_sys_prompt = ""
            try:
                if os.path.exists(self.default_workflow_path):
                    with open(self.default_workflow_path, 'r', encoding='utf-8') as f:
                        wf = json.load(f)
                        if "35" in wf and "inputs" in wf["35"]:
                            default_sys_prompt = wf["35"]["inputs"].get("system_prompt", "")
            except: pass
            if default_sys_prompt:
                self.text_sys_prompt.setPlainText(default_sys_prompt)

