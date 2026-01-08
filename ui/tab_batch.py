from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QComboBox, QGroupBox, QSplitter, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from pathlib import Path
from PIL import Image, ImageOps
from core.utils import config_helper
from ui.styles import Styles, Colors
from ui.widgets.path_selector import PathSelectorWidget
from ui.widgets.image_compare import ImageCompareWidget
from ui.widgets.console_log import ConsoleLogWidget
from core.workers.batch_worker import BatchWorker
from ui.base_tab import BaseTab

# Empirically Verified Resolution Table (Truth Table)
RESOLUTION_TABLE = {
    "1:1":  {"1K": (1024, 1024), "2K": (2048, 2048), "4K": (4096, 4096)},
    "16:9": {"1K": (1376, 768),  "2K": (2752, 1536), "4K": (5504, 3072)},
    "9:16": {"1K": (768, 1376),  "2K": (1536, 2752), "4K": (3072, 5504)},
    "4:3":  {"1K": (1200, 896),  "2K": (2400, 1792), "4K": (4800, 3584)},
    "3:4":  {"1K": (896, 1200),  "2K": (1792, 2400), "4K": (3584, 4800)},
    "3:2":  {"1K": (1264, 848),  "2K": (2528, 1696), "4K": (5056, 3392)},
    "2:3":  {"1K": (848, 1264),  "2K": (1696, 2528), "4K": (3392, 5056)},
    "5:4":  {"1K": (1152, 928),  "2K": (2304, 1856), "4K": (4608, 3712)},
    "4:5":  {"1K": (928, 1152),  "2K": (1856, 2304), "4K": (3712, 4608)},
    "21:9": {"1K": (1584, 672),  "2K": (3168, 1344), "4K": (6336, 2688)}
}

class TabBatch(BaseTab):
    """
    UI for batch image processing.
    
    Features:
    - Path selection for Input (Images) and Output (Generation)
    - Grid validation and auto-cropping/optimization
    - Live progress tracking with ETA and logging
    - Preview comparing input vs output
    """
    def __init__(self):
        super().__init__()
        self.worker = None
        self.MODEL_ID = "gemini-3-pro-image-preview"
        self.scan_results = None
        self.api_limit = 250
        
        self.setStyleSheet(Styles.GLOBAL + Styles.INPUT_FIELD + Styles.SECTION_HEADER + Styles.BTN_BASE)
        
        self._setup_ui()
        self._register_fields()
        self.load_state()
        self.check_api_usage()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- LEFT PANEL (Controls) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Grid Validator
        grp_validator = QGroupBox("📋 Image Grid Validator (64px)")
        l_validator = QVBoxLayout()
        
        h_val = QHBoxLayout()
        self.btn_scan = QPushButton("🔍 ANALYZE")
        self.btn_scan.setStyleSheet(Styles.BTN_ACCENT)
        self.btn_scan.clicked.connect(self.scan_images)
        h_val.addWidget(self.btn_scan)
        
        self.btn_crop = QPushButton("🍌 OPTIMIZE")
        self.btn_crop.setStyleSheet(Styles.BTN_PRIMARY)
        self.btn_crop.clicked.connect(self.auto_crop_images)
        self.btn_crop.setEnabled(False)
        h_val.addWidget(self.btn_crop)
        l_validator.addLayout(h_val)
        
        self.validator_report = QTextEdit()
        self.validator_report.setReadOnly(True)
        self.validator_report.setMaximumHeight(100)
        self.validator_report.setStyleSheet(Styles.TEXT_AREA_CONSOLE)
        self.validator_report.setPlaceholderText("Scan to check alignment...")
        l_validator.addWidget(self.validator_report)
        
        grp_validator.setLayout(l_validator)
        left_layout.addWidget(grp_validator)
        
        # 2. Paths
        grp_paths = QGroupBox("Paths & Settings")
        l_paths = QVBoxLayout() # Changed to VBox for widgets
        l_paths.setSpacing(10)
        
        self.path_in = PathSelectorWidget("Input Root:", select_file=False)
        l_paths.addWidget(self.path_in)
        
        self.path_out = PathSelectorWidget("Output Folder:", select_file=False)
        l_paths.addWidget(self.path_out)

        # Settings Row
        h_set = QHBoxLayout()
        
        h_set.addWidget(QLabel("Res:"))
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1K", "2K", "4K"])
        h_set.addWidget(self.combo_res)
        
        h_set.addWidget(QLabel("Ratio:"))
        self.combo_ratio = QComboBox()
        self.combo_ratio.addItems(["Auto", "Manual"])
        h_set.addWidget(self.combo_ratio)

        h_set.addWidget(QLabel("Fmt:"))
        self.combo_fmt = QComboBox()
        self.combo_fmt.addItems(["PNG", "JPG"])
        h_set.addWidget(self.combo_fmt)
        
        self.lbl_api_counter = QLabel("RDP: ...")
        self.lbl_api_counter.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-weight: bold; margin-left: 10px;")
        h_set.addWidget(self.lbl_api_counter)
        
        h_set.addStretch()
        l_paths.addLayout(h_set)
        grp_paths.setLayout(l_paths)
        left_layout.addWidget(grp_paths)

        # 3. Status Log
        self.log_widget = ConsoleLogWidget()
        left_layout.addWidget(self.log_widget)
        
        # 4. Progress & ETA
        h_prog = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setValue(0)
        h_prog.addWidget(self.progress)
        
        self.lbl_eta = QLabel("ETA: --:--")
        self.lbl_eta.setStyleSheet(f"font-weight: bold; color: {Colors.TEXT_MUTED};")
        h_prog.addWidget(self.lbl_eta)
        left_layout.addLayout(h_prog)

        # 5. Buttons
        h_btns = QHBoxLayout()
        self.btn_start = QPushButton("START PROCESSING")
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
        
        # Image Comparison Widget
        self.img_compare = ImageCompareWidget()
        l_preview.addWidget(self.img_compare, 3) # Takes more space

        # Prompt Display
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
        """Register all stateful widgets with BaseTab"""
        self.register_field("input_path", self.path_in)
        self.register_field("output_path", self.path_out)
        self.register_field("resolution", self.combo_res)
        self.register_field("aspect_ratio", self.combo_ratio)
        self.register_field("output_format", self.combo_fmt)

    def save_settings(self):
        """Simplified - uses BaseTab's automated save"""
        super().save_state()

    def load_state(self):
        """Simplified - uses BaseTab's automated load"""
        super().load_state()

    def start_process(self):
        key = config_helper.get_value("api_key", "")
        in_path = self.path_in.get_path()
        out_path = self.path_out.get_path()
        
        if not key or not in_path:
            self.log_widget.append_log("[ERROR] Invalid API Key or Input Path")
            return

        self.save_settings()
        self.log_widget.clear_log()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setValue(0)
        self.lbl_eta.setText("ETA: ...")
        
        self.img_compare.clear()
        self.txt_prompt.clear()

        # Create worker
        self.worker = BatchWorker(
            key, in_path, out_path,
            self.combo_res.currentText(), self.combo_ratio.currentText(),
            self.combo_fmt.currentText(),
            self.MODEL_ID, True, # logs always valid now
            parent=self
        )
        self.worker.log_signal.connect(self.log_widget.append_log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.time_estimate_signal.connect(self.lbl_eta.setText)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error_signal.connect(lambda e: self.log_widget.append_log(f"CRITICAL ERROR: {e}"))
        self.worker.preview_signal.connect(self.update_preview)
        self.worker.api_call_signal.connect(self.increment_api_usage)
        
        self.worker.start()

    def stop_process(self):
        if self.worker:
            self.log_widget.append_log("!!! STOP REQUESTED !!!")
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

    def scan_images(self):
        input_path = self.path_in.get_path()
        if not input_path or not Path(input_path).exists():
            self.validator_report.setText("❌ Select valid input folder!")
            return
        
        # Reuse logic but keep it concise here or extract to Utils if repeated
        # Keeping core logic here as requested to not over-engineer if unique
        input_dir = Path(input_path)
        valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
        
        projects = []
        if (input_dir / "prompts.md").exists():
            projects = [input_dir]
        else:
            projects = [d for d in input_dir.iterdir() if d.is_dir()]
        
        if not projects:
             self.validator_report.setText("⚠️ No project folders found.")
             return

        optimized_plan = []
        target_quality = self.combo_res.currentText()
        
        for project_dir in projects:
             for img_file in project_dir.iterdir():
                if img_file.suffix.lower() in valid_exts and img_file.is_file():
                    try:
                        with Image.open(img_file) as img:
                            w, h = img.size
                            curr_ratio = w / h
                            
                            def parse_ratio(r_str):
                                p = r_str.split(':')
                                return int(p[0]) / int(p[1])
                            
                            best_ratio = min(RESOLUTION_TABLE.keys(), key=lambda r: abs(curr_ratio - parse_ratio(r)))
                            target = RESOLUTION_TABLE[best_ratio][target_quality]
                            
                            optimized_plan.append({
                                'name': img_file.name,
                                'path': img_file,
                                'project_dir': project_dir,
                                'target': target,
                                'ratio': best_ratio,
                                'optimized': (w == target[0] and h == target[1])
                            })
                    except: pass
        
        self.scan_results = {'input_dir': input_dir, 'plan': optimized_plan}
        
        ready = len([p for p in optimized_plan if p['optimized']])
        total = len(optimized_plan)
        report = f"📊 REPORT ({target_quality})\nTotal: {total} | Ready: {ready} | Needs Opt: {total - ready}\n"
        
        if total - ready > 0:
            report += "💡 Click 'OPTIMIZE' to fix resolutions."
            self.btn_crop.setEnabled(True)
        else:
            report += "✅ All perfect!"
            self.btn_crop.setEnabled(False)
            
        self.validator_report.setText(report)

    def auto_crop_images(self):
        if not self.scan_results: return
        
        self.validator_report.append("\n🚀 OPTIMIZING...")
        processed = 0
        input_dir = self.scan_results['input_dir']
        
        for p in self.scan_results['plan']:
            if p['optimized']: continue
            try:
                with Image.open(p['path']) as img:
                    if img.mode != 'RGB': img = img.convert('RGB')
                    new_img = ImageOps.fit(img, p['target'], method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    
                    p_dir = p.get('project_dir', input_dir)
                    out_dir = p_dir / "optimized"
                    out_dir.mkdir(exist_ok=True)
                    
                    save_name = f"{p['name'].rsplit('.', 1)[0]}_optimized.{p['name'].split('.')[-1]}"
                    new_img.save(out_dir / save_name, quality=95)
                    processed += 1
            except: pass
            
        self.validator_report.append(f"✅ DONE! Optimized {processed} images.")
        self.scan_results = None
        self.btn_crop.setEnabled(False)

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
