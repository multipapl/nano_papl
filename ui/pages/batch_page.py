import os
import json
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt, QDate

from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition, themeColor
from ui.components import ThemeAwareBackground

# Shared Managers/Utils
from core.utils import config_helper
from core import constants

# Workers
from core.workers.batch_worker import BatchWorker
from core.workers.comfy_worker import ComfyWorker

# Modular Widgets
from ui.widgets.batch import ConfigPanel, MonitoringPanel

class BatchPage(ThemeAwareBackground):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BatchPage")
        self.worker = None
        self.MODEL_ID = "gemini-3-pro-image-preview"
        self.api_limit = 250
        self.default_workflow_path = "data/api_nano_banana_pro.json"
        
        self._init_ui()
        self.config_panel.load_state()
        self.check_api_usage()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for Main Content
        self.splitter = QSplitter(Qt.Horizontal, self)
        
        # --- LEFT COLUMN (Config) ---
        self.left_scroll = ScrollArea()
        self.left_scroll.setWidgetResizable(True)
        from ui.components import get_scroll_style
        self.left_scroll.setStyleSheet(get_scroll_style())
        self.left_scroll.viewport().setStyleSheet("background: transparent;")
        
        self.config_panel = ConfigPanel()
        self.config_panel.setStyleSheet("background: transparent;")
        self.left_scroll.setWidget(self.config_panel)
        self.splitter.addWidget(self.left_scroll)
        
        # --- RIGHT COLUMN (Monitor) ---
        self.monitor_panel = MonitoringPanel()
        self.monitor_panel.setStyleSheet("background: transparent;")
        self.splitter.addWidget(self.monitor_panel)
        
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 6)
        
        main_layout.addWidget(self.splitter)
        
        # Connect Signals from Panels
        self.monitor_panel.btn_start.clicked.connect(self.start_process)
        self.monitor_panel.btn_stop.clicked.connect(self.stop_process)

    # --- Logic ---

    def start_process(self):
        state = self.config_panel.get_state()
        in_path = state["batch_input_path"]
        out_path = state["batch_output_path"]
        
        if not in_path:
            self.append_log("[ERROR] Invalid Input Path")
            return

        self._save_state()
        self.monitor_panel.set_busy(True)
        
        engine_idx = state["batch_engine"]
        if engine_idx == 0: # Google Gemini
            self._start_gemini(in_path, out_path)
        else:
            self._start_comfy(in_path, out_path)

    def _start_gemini(self, in_path, out_path):
        key = config_helper.get_value("api_key", "")
        if not key:
            self.append_log("[ERROR] Gemini API Key missing in Settings")
            self.on_finished()
            return
            
        state = self.config_panel.get_state()
        res_text = self.config_panel.combo_res.currentText()
        ratio_text = self.config_panel.combo_ratio.currentText()
        fmt_text = self.config_panel.combo_fmt.currentText()

        self.worker = BatchWorker(
            key, in_path, out_path,
            res_text, ratio_text,
            fmt_text,
            self.MODEL_ID, True,
            parent=self
        )
        self._connect_signals()
        self.worker.time_estimate_signal.connect(self.monitor_panel.lbl_eta.setText)
        self.worker.api_call_signal.connect(self.increment_api_usage)
        self.worker.start()

    def _start_comfy(self, in_path, out_path):
        if not out_path:
            self.append_log("[ERROR] Output Path required for ComfyUI")
            self.on_finished()
            return

        state = self.config_panel.get_state()
        settings = {
            "comfy_url": config_helper.get_value("comfy_url", "http://127.0.0.1:8188"),
            "api_key": config_helper.get_value("comfy_api_key", ""),
            "input_path": in_path,
            "output_path": out_path,
            "resolution": self.config_panel.combo_res.currentText(),
            "ratio": self.config_panel.combo_ratio.currentText(),
            "dry_run": self.config_panel.check_dry_run.isChecked(),
            "workflow_path": self.default_workflow_path,
            "system_prompt": self.config_panel.text_sys_prompt.toPlainText(),
            "use_random_seed": self.config_panel.check_random_seed.isChecked(),
            "seed_value": self.config_panel.spin_seed.value()
        }
        
        self.worker = ComfyWorker(settings)
        self._connect_signals()
        self.worker.start()

    def _connect_signals(self):
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.monitor_panel.progress.setValue)
        self.worker.preview_signal.connect(self.monitor_panel.update_preview)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(lambda e: self.append_log(f"CRITICAL ERROR: {e}"))
        self.worker.finished.connect(self.worker.deleteLater)

    def stop_process(self):
        if self.worker:
            self.append_log("Stopping process...")
            if hasattr(self.worker, 'stop'): self.worker.stop()
            elif hasattr(self.worker, 'request_stop'): self.worker.request_stop()
            self.monitor_panel.btn_stop.setEnabled(False)

    def on_finished(self):
        self.monitor_panel.set_busy(False)
        self.monitor_panel.lbl_eta.setText("ETA: Done")
        self.worker = None

    def append_log(self, text):
        self.monitor_panel.append_log(text)

    # --- State & API ---

    def _save_state(self):
        state = self.config_panel.get_state()
        for k, v in state.items():
            config_helper.set_value(k, v)

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
        self.config_panel.lbl_api_counter.setText(f"RDP Daily Usage: {count}/{self.api_limit}")
        color = themeColor().name() if count < self.api_limit else "#d32f2f"
        self.config_panel.lbl_api_counter.setStyleSheet(f"color: {color}; font-weight: bold;")
