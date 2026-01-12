import os
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QComboBox, QGroupBox, QSplitter, 
    QCheckBox, QSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, QDate

from core.utils import config_helper
from ui.styles import Styles, Colors
from ui.base_tab import BaseTab

# Widgets
from ui.widgets.path_selector import PathSelectorWidget
from ui.widgets.image_compare import ImageCompareWidget
from ui.widgets.console_log import ConsoleLogWidget

# Workers
from core.workers.batch_worker import BatchWorker
from core.workers.comfy_worker import ComfyWorker

class TabBatch(BaseTab):
    """
    Unified Batch Generation Tab.
    Supports:
    1. Gemini Cloud Generation (Text-to-Image via Google GenAI)
    2. ComfyUI Local Generation (via Local API)
    """
    def __init__(self):
        super().__init__()
        self.worker = None
        self.MODEL_ID = "gemini-3-pro-image-preview"
        self.api_limit = 250
        self.default_workflow_path = "data/api_nano_banana_pro.json"
        
        self.setStyleSheet(Styles.GLOBAL + Styles.INPUT_FIELD + Styles.SECTION_HEADER + Styles.BTN_BASE)
        
        self._setup_ui()
        self._register_fields()
        self.load_state()
        self.check_api_usage()
        
        # Trigger initial visibility update
        self._on_engine_changed(self.combo_engine.currentText())

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- LEFT PANEL (Controls) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Engine Selection
        grp_engine = QGroupBox("Generation Engine")
        l_engine = QHBoxLayout()
        self.combo_engine = QComboBox()
        self.combo_engine.addItems(["Google (API)", "Comfy (API)"])
        self.combo_engine.currentTextChanged.connect(self._on_engine_changed)
        l_engine.addWidget(self.combo_engine)
        grp_engine.setLayout(l_engine)
        left_layout.addWidget(grp_engine)
        
        # 2. Paths & Shared Settings
        grp_paths = QGroupBox("Configuration")
        l_config = QVBoxLayout()
        l_config.setSpacing(10)
        
        self.path_in = PathSelectorWidget("Input Root:", select_file=False)
        l_config.addWidget(self.path_in)
        
        self.path_out = PathSelectorWidget("Output Folder:", select_file=False)
        l_config.addWidget(self.path_out)


        # Shared Params Row
        h_params = QHBoxLayout()
        h_params.setContentsMargins(0, 0, 0, 0)
        h_params.setSpacing(10)
        h_params.setAlignment(Qt.AlignLeft)
        
        # Res
        lbl_res = QLabel("Res:")
        lbl_res.setFixedWidth(40)
        lbl_res.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-weight: bold;")
        h_params.addWidget(lbl_res)

        self.combo_res = QComboBox()
        self.combo_res.setFixedWidth(90)
        self.combo_res.addItems(["1K", "2K", "4K"])
        h_params.addWidget(self.combo_res)
        
        # Ratio
        lbl_ratio = QLabel("Ratio:")
        lbl_ratio.setFixedWidth(40)
        lbl_ratio.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-weight: bold;")
        h_params.addWidget(lbl_ratio)

        self.combo_ratio = QComboBox()
        self.combo_ratio.setFixedWidth(90)
        self.combo_ratio.addItems(["Auto", "Manual", "1:1", "16:9", "9:16", "4:5", "3:4"]) 
        h_params.addWidget(self.combo_ratio)
        
        h_params.addStretch()
        
        l_config.addLayout(h_params)
        
        # --- ENGINE SPECIFIC CONTROLS (STACKED) ---
        from PySide6.QtWidgets import QStackedWidget
        self.stack_engine_controls = QStackedWidget()
        self.stack_engine_controls.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed) # Prevent jumping
        
        # PAGE 1: Google (API)
        page_google = QWidget()
        l_google = QVBoxLayout(page_google)
        l_google.setContentsMargins(0, 0, 0, 0)
        
        h_google = QHBoxLayout()
        h_google.setContentsMargins(0, 0, 0, 0)
        h_google.setSpacing(10)
        h_google.setAlignment(Qt.AlignLeft)

        self.lbl_fmt = QLabel("Fmt:")
        self.lbl_fmt.setFixedWidth(40)
        self.lbl_fmt.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-weight: bold;")
        h_google.addWidget(self.lbl_fmt)

        self.combo_fmt = QComboBox()
        self.combo_fmt.setFixedWidth(90)
        self.combo_fmt.addItems(["PNG", "JPG"])
        h_google.addWidget(self.combo_fmt)
        
        # Spacer to align with Ratio column (40 + 90 + spacing)
        # We want the counter to start where Ratio label starts or slightly after
        # Just adding the counter here usually works if left-aligned
        
        self.lbl_api_counter = QLabel("RDP: ...")
        self.lbl_api_counter.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-weight: bold; margin-left: 10px;")
        h_google.addWidget(self.lbl_api_counter)
        h_google.addStretch()
        l_google.addLayout(h_google)
        
        # PAGE 2: Comfy (API)
        page_comfy = QWidget()
        l_comfy = QVBoxLayout(page_comfy)
        l_comfy.setContentsMargins(0, 0, 0, 0)
        
        # Seed Row
        h_seed = QHBoxLayout()
        h_seed.setContentsMargins(0, 0, 0, 0)
        h_seed.setSpacing(10)
        h_seed.setAlignment(Qt.AlignLeft)
        
        self.check_random_seed = QCheckBox("Random Seed")
        self.check_random_seed.setChecked(True)
        self.check_random_seed.toggled.connect(self._toggle_seed_input)
        
        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 999999999)
        self.spin_seed.setValue(123456789)
        self.spin_seed.setEnabled(False)
        self.spin_seed.setMinimumWidth(120)
        
        h_seed.addWidget(self.spin_seed)
        h_seed.addWidget(self.check_random_seed)
        h_seed.addStretch()
        l_comfy.addLayout(h_seed)

        # System Prompt
        lbl_sys = QLabel("System Prompt Override:")
        lbl_sys.setStyleSheet("font-size: 10px; color: #888;")
        l_comfy.addWidget(lbl_sys)
        
        self.text_sys_prompt = QTextEdit()
        self.text_sys_prompt.setPlaceholderText("Override workflow default...")
        self.text_sys_prompt.setFixedHeight(60) # Compact height
        l_comfy.addWidget(self.text_sys_prompt)
        
        # Add pages
        self.stack_engine_controls.addWidget(page_google) # Index 0
        self.stack_engine_controls.addWidget(page_comfy)  # Index 1
        
        l_config.addWidget(self.stack_engine_controls)
        grp_paths.setLayout(l_config)
        
        left_layout.addWidget(grp_paths)

        # 4. Logs
        self.log_widget = ConsoleLogWidget()
        left_layout.addWidget(self.log_widget)
        
        # 5. Progress & Action
        h_prog = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setValue(0)
        h_prog.addWidget(self.progress)
        
        self.lbl_eta = QLabel("ETA: --:--")
        self.lbl_eta.setStyleSheet(f"font-weight: bold; color: {Colors.TEXT_MUTED};")
        h_prog.addWidget(self.lbl_eta)
        left_layout.addLayout(h_prog)

        h_btns = QHBoxLayout()
        
        # Comfy Dry Run (Moved to bottom button area, visible only for Comfy?)
        # Or keep in stack? User screenshot showed it at bottom.
        # I will make it visible/hidden based on engine but place it here.
        self.check_dry_run = QCheckBox("Dry Run")
        self.check_dry_run.setToolTip("Uploads resources but does not generate images.")
        self.check_dry_run.setChecked(False) # Default OFF per request
        self.check_dry_run.setStyleSheet("font-weight: bold; color: #E0E0E0; margin-right: 15px;")
        h_btns.addWidget(self.check_dry_run)

        self.btn_start = QPushButton("START BATCH")
        self.btn_start.setMinimumHeight(45)
        self.btn_start.setStyleSheet(Styles.BTN_PRIMARY)
        self.btn_start.clicked.connect(self.start_process)
        h_btns.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setMinimumHeight(45)
        self.btn_stop.setStyleSheet(Styles.BTN_DANGER)
        self.btn_stop.clicked.connect(self.stop_process)
        self.btn_stop.setEnabled(False)
        h_btns.addWidget(self.btn_stop)
        
        left_layout.addLayout(h_btns)

        # --- RIGHT PANEL (Preview) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        grp_preview = QGroupBox("Live Preview")
        l_preview = QVBoxLayout()
        
        self.img_compare = ImageCompareWidget()
        l_preview.addWidget(self.img_compare, 3)

        lbl_p = QLabel("Current Prompt:")
        lbl_p.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px; font-weight: bold;")
        l_preview.addWidget(lbl_p)

        self.txt_prompt = QTextEdit()
        self.txt_prompt.setReadOnly(True)
        self.txt_prompt.setStyleSheet("background-color: #2b2b2b; color: #ccc; font-style: italic; border: 1px solid #3d3d3d;")
        l_preview.addWidget(self.txt_prompt, 1)
        
        grp_preview.setLayout(l_preview)
        right_layout.addWidget(grp_preview)

        # --- COMBINE ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        
        main_layout.addWidget(splitter)
    
    def _register_fields(self):
        """Register all stateful widgets"""
        self.register_field("batch_engine", self.combo_engine)
        self.register_field("input_path", self.path_in)
        self.register_field("output_path", self.path_out)
        self.register_field("resolution", self.combo_res)
        self.register_field("aspect_ratio", self.combo_ratio)
        self.register_field("output_format", self.combo_fmt)
        
        # Comfy specific
        self.register_field("comfy_sys_prompt", self.text_sys_prompt)
        self.register_field("comfy_random_seed", self.check_random_seed)
        self.register_field("comfy_seed_value", self.spin_seed)
        self.register_field("comfy_dry_run", self.check_dry_run)

    def _on_engine_changed(self, text):
        is_gemini = "Google" in text
        is_comfy = "Comfy" in text
        
        # Switch Stack Page
        self.stack_engine_controls.setCurrentIndex(0 if is_gemini else 1)
        
        # Toggle Dry Run Visibility (only for Comfy)
        self.check_dry_run.setVisible(is_comfy)
        
        if is_comfy:
            self._load_comfy_defaults()

    def _toggle_seed_input(self, checked):
        self.spin_seed.setEnabled(not checked)
        if not checked:
            self.spin_seed.setFocus()

    def _load_comfy_defaults(self):
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

    def start_process(self):
        engine = self.combo_engine.currentText()
        in_path = self.path_in.get_path()
        out_path = self.path_out.get_path()
        
        if not in_path:
            self.log_widget.append_log("[ERROR] Invalid Input Path")
            return

        self.save_state()
        self.log_widget.clear_log()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setValue(0)
        self.lbl_eta.setText("ETA: ...")
        self.img_compare.clear()
        self.txt_prompt.clear()
        
        if "Google" in engine:
            self._start_gemini(in_path, out_path)
        else:
            self._start_comfy(in_path, out_path)

    def _start_gemini(self, in_path: str, out_path: str) -> None:
        key = config_helper.get_value("api_key", "")
        if not key:
            self.log_widget.append_log("[ERROR] API Key required for Gemini")
            self._on_finished()
            return
            
        self.worker = BatchWorker(
            key, in_path, out_path,
            self.combo_res.currentText(), self.combo_ratio.currentText(),
            self.combo_fmt.currentText(),
            self.MODEL_ID, True,
            parent=self
        )
        self._connect_common_signals()
        self.worker.time_estimate_signal.connect(self.lbl_eta.setText) # Gemini only feature currently
        self.worker.preview_signal.connect(self.update_preview)
        self.worker.api_call_signal.connect(self.increment_api_usage)
        self.worker.start()

    def _start_comfy(self, in_path: str, out_path: str) -> None:
        if not out_path:
             self.log_widget.append_log("[ERROR] Output Path required for ComfyUI")
             self._on_finished()
             return

        batch_settings = {
            "comfy_url": config_helper.get_value("comfy_url", "http://127.0.0.1:8188"),
            "api_key": config_helper.get_value("comfy_api_key", ""), # Future proofing
            "input_path": in_path,
            "output_path": out_path,
            "resolution": self.combo_res.currentText(),
            "ratio": self.combo_ratio.currentText(),
            "dry_run": self.check_dry_run.isChecked(),
            "workflow_path": self.default_workflow_path,
            "system_prompt": self.text_sys_prompt.toPlainText(),
            "use_random_seed": self.check_random_seed.isChecked(),
            "seed_value": self.spin_seed.value()
        }
        
        self.worker = ComfyWorker(batch_settings)
        self._connect_common_signals()
        self.worker.preview_signal.connect(self.update_preview) # Added Connection
        self.worker.start()

    def _connect_common_signals(self):
        self.worker.log_signal.connect(self.log_widget.append_log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(lambda e: self.log_widget.append_log(f"CRITICAL ERROR: {e}"))
        self.worker.finished.connect(self.worker.deleteLater)

    def stop_process(self):
        if self.worker:
            self.log_widget.append_log("!!! STOP REQUESTED !!!")
            # Both workers support stop()/request_stop() differently?
            # ComfyWorker has stop(), BatchWorker has request_stop()
            # Let's standardize or check type.
            if hasattr(self.worker, 'stop'):
                self.worker.stop()
            elif hasattr(self.worker, 'request_stop'):
                self.worker.request_stop()
            self.btn_stop.setEnabled(False)

    def on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_eta.setText("ETA: Done")
        self.worker = None

    def update_preview(self, in_path, out_path, prompt):
        self.txt_prompt.setText(prompt)
        self.img_compare.set_input(in_path)
        self.img_compare.set_output(out_path)

    # API Counter Logic (Shared/Gemini)
    def check_api_usage(self):
        today = QDate.currentDate().toString(Qt.ISODate)
        data = config_helper.get_value("api_usage", {})
        if data.get("date") != today:
            data = {"date": today, "count": 0}
            config_helper.set_value("api_usage", data)
        self._update_api_label(data["count"])

    def increment_api_usage(self):
        today = QDate.currentDate().toString(Qt.ISODate)
        data = config_helper.get_value("api_usage", {})
        if data.get("date") != today: data = {"date": today, "count": 0}
        
        data["count"] = data.get("count", 0) + 1
        config_helper.set_value("api_usage", data)
        self._update_api_label(data["count"])

    def _update_api_label(self, count):
        self.lbl_api_counter.setText(f"RDP: {count}/{self.api_limit}")
        color = "#2da44e" if count < self.api_limit else "#d32f2f"
        self.lbl_api_counter.setStyleSheet(f"color: {color}; font-weight: bold; margin-left: 10px;")
