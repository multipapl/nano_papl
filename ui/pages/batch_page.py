import os
import json
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt, QDate
from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition, themeColor
from ui.components import ThemeAwareBackground
import time

# Shared Managers/Utils
from core.utils import config_helper
from core import constants

# Workers
from core.workers.batch_worker import BatchWorker
from core.workers.comfy_worker import ComfyWorker

from ui.components import NPBasePage
from ui.widgets.batch import ConfigPanel, MonitoringPanel

class BatchPage(NPBasePage):
    """
    Refactored Batch Page inheriting from NPBasePage.
    Coordinates between engine workers and specialized UI panels.
    """
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("BatchPage")
        self.config_manager = config_manager
        self.worker = None
        self.MODEL_ID = "gemini-3-pro-image-preview"
        self.api_limit = 250
        self.default_workflow_path = "data/api_nano_banana_pro.json"
        
        self._init_ui()
        self.config_panel.load_state()
        self.check_api_usage()
        
    def _init_ui(self):
        # NPBasePage already provides self.main_layout with zero margins

        # Splitter for Main Content
        self.splitter = QSplitter(Qt.Horizontal, self)
        
        # --- LEFT COLUMN (Config) ---
        self.config_panel = ConfigPanel()
        self.config_panel.setStyleSheet("background: transparent;")
        
        # Use NPBasePage utility for content scroll area
        self.left_scroll = self.addScrollArea(self.config_panel)
        # Note: addScrollArea adds it to main_layout, but we want it in the splitter.
        # We need to take it out of main_layout or change logic.
        
        # Correction: NPBasePage.addScrollArea is too generic. Let's do it manually 
        # but using the same style.
        from ui.components import get_scroll_style
        self.left_scroll.setStyleSheet(get_scroll_style())
        
        self.splitter.addWidget(self.left_scroll)
        
        # --- RIGHT COLUMN (Monitor) ---
        self.monitor_panel = MonitoringPanel()
        self.monitor_panel.setStyleSheet("background: transparent;")
        self.splitter.addWidget(self.monitor_panel)
        
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 6)
        
        self.main_layout.addWidget(self.splitter)
        
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
        self.start_time = time.time() # Start timing
        
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
        gen_cfg = self.config_panel.gen_config.get_config()
        res_text = gen_cfg["res"]
        ratio_text = gen_cfg["ratio"]
        fmt_text = gen_cfg["format"]

        # Get timeout from config
        timeout = self.config_manager.config.api_timeout

        self.worker = BatchWorker(
            key, in_path, out_path,
            res_text, ratio_text,
            fmt_text,
            self.MODEL_ID, state.get("batch_save_logs", True),
            timeout, # Pass timeout
            parent=self
        )
        self._connect_signals()
        self.worker.time_estimate_signal.connect(self.monitor_panel.lbl_eta.setText)
        self.worker.api_call_signal.connect(self.increment_api_usage)
        
        self.showStateToolTip("Batch Generation", "Gemini is processing projects...")
        self.worker.start()

    def _start_comfy(self, in_path, out_path):
        if not out_path:
            self.append_log("[ERROR] Output Path required for ComfyUI")
            self.on_finished()
            return

        state = self.config_panel.get_state()
        gen_cfg = self.config_panel.gen_config.get_config()
        settings = {
            "comfy_url": self.config_manager.config.comfy_url or constants.DEFAULT_COMFY_URL,
            "api_key": self.config_manager.config.comfy_api_key,
            "input_path": in_path,
            "output_path": out_path,
            "resolution": gen_cfg["res"],
            "ratio": gen_cfg["ratio"],
            "dry_run": self.config_panel.check_dry_run.isChecked(),
            "workflow_path": self.default_workflow_path,
            "system_prompt": self.config_panel.text_sys_prompt.toPlainText(),
            "use_random_seed": self.config_panel.check_random_seed.isChecked(),
            "seed_value": self.config_panel.spin_seed.value(),
            "save_logs": state.get("batch_save_logs", True)
        }
        
        self.worker = ComfyWorker(settings)
        self._connect_signals()
        
        self.showStateToolTip("ComfyUI Generation", "Backend is processing...")
        self.worker.start()

    def _connect_signals(self):
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.monitor_panel.progress.setValue)
        self.worker.preview_signal.connect(self.monitor_panel.update_preview)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.handle_critical_error)
        self.worker.finished.connect(self.worker.deleteLater)

    def handle_critical_error(self, e):
        self.append_log(f"CRITICAL ERROR: {e}")
        self.finishStateToolTip("Error", "Generation failed")

    def stop_process(self):
        if self.worker:
            self.append_log("Stopping process...")
            if hasattr(self.worker, 'stop'): self.worker.stop()
            elif hasattr(self.worker, 'request_stop'): self.worker.request_stop()
            self.monitor_panel.btn_stop.setEnabled(False)
            # Save RPD counter state if stopped manually
            self.config_manager.save()

    def on_finished(self):
        self.monitor_panel.set_busy(False)
        self.monitor_panel.lbl_eta.setText("ETA: Done")
        self.finishStateToolTip("Generation Finished", "All tasks completed successfully")
        self.worker = None
        
        # Save RPD counter state
        self.config_manager.save()

    def append_log(self, text):
        self.monitor_panel.append_log(text)

    # --- State & API ---

    def _save_state(self):
        state = self.config_panel.get_state()
        for k, v in state.items():
            if hasattr(self.config_manager.config, k):
                setattr(self.config_manager.config, k, v)
            else:
                self.config_manager.config._extra[k] = v
        self.config_manager.save()

    def check_api_usage(self):
        """Checks and resets API usage if the day has changed."""
        today = QDate.currentDate().toString(Qt.ISODate)
        config = self.config_manager.config
        
        # Ensure we work with a dictionary, not a string (if config was corrupted)
        data = config.api_usage
        if not isinstance(data, dict):
            data = {}
            
        stored_date = data.get("date", "")
        
        # Reset if date changed or date is missing
        if stored_date != today:
            data = {"date": today, "count": 0}
            config.api_usage = data
            self.config_manager.save()
            
        self._update_api_label(data["count"])

    def increment_api_usage(self):
        """Increments the daily counter safely."""
        today = QDate.currentDate().toString(Qt.ISODate)
        config = self.config_manager.config
        
        data = config.api_usage
        if not isinstance(data, dict):
            data = {}
            
        # Double-check date in case app ran across midnight
        if data.get("date") != today:
            data = {"date": today, "count": 0}
            
        data["count"] = data.get("count", 0) + 1
        config.api_usage = data
        # Optimization: Don't save on every increment to avoid IO lag
        # self.config_manager.save() 
        self._update_api_label(data["count"])

    def _update_api_label(self, count):
        from ui.components import UIConfig
        self.config_panel.lbl_api_counter.setText(f"RPD Daily Usage: {count}/{self.api_limit}")
        color = themeColor().name() if count < self.api_limit else UIConfig.DANGER_COLOR
        self.config_panel.lbl_api_counter.setStyleSheet(f"color: {color}; font-weight: bold;")
