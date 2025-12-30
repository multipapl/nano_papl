from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, 
    QProgressBar, QTextEdit, QFileDialog, QCheckBox, QComboBox, QGroupBox, QMenu,
    QFrame, QSizePolicy, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QUrl, QSize
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QResizeEvent
import datetime
import math
import re
from pathlib import Path
from PIL import Image, ImageOps
from google import genai
from google.genai import types
from utils import config_helper

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

# --- Custom Widgets ---
class DragDropLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            path = url.toLocalFile()
            if path:
                self.setText(path)
                event.acceptProposedAction()

class ResizingLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px dashed #444; color: #666;")
        self.setMinimumSize(250, 250)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(self.scaledPixmap())

    def resizeEvent(self, event: QResizeEvent):
        if self._pixmap:
            super().setPixmap(self.scaledPixmap())
        super().resizeEvent(event)

    def scaledPixmap(self):
        if not self._pixmap: return QPixmap()
        return self._pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

# --- Worker Thread ---
class BatchWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(float)
    finished_signal = Signal()
    error_signal = Signal(str)
    preview_signal = Signal(str, str, str) # input_path, output_path, prompt_text

    def __init__(self, api_key, input_path, output_path, resolution, ratio, model_id, check_logs, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else self.input_path / "_renders"
        self.resolution = resolution
        self.ratio = ratio
        self.model_id = model_id
        self.check_logs = check_logs
        self.stop_requested = False
        self.PROMPT_FILENAME = "prompts.md"

    def run(self):
        self.log_signal.emit("--- INITIALIZING BATCH PROCESS ---")
        try:
            client = genai.Client(api_key=self.api_key)
            
            # --- Smart Folder Logic ---
            projects = []
            
            # Check 1: Is the input path itself a project?
            if (self.input_path / self.PROMPT_FILENAME).exists():
                self.log_signal.emit(f"Detected Single Project Mode: {self.input_path.name}")
                projects = [self.input_path]
            else:
                # Check 2: It's a root folder with subprojects
                projects = [d for d in self.input_path.iterdir() if d.is_dir()]
            
            if not projects:
                self.log_signal.emit("WARNING: No project folders found (checked for prompts.md).")
            
            valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
            
            for project_dir in projects:
                if self.stop_requested: break

                # Smart Image Source: Prefer 'optimized' folder if it exists
                image_source_dir = project_dir / "optimized"
                if not image_source_dir.exists():
                    image_source_dir = project_dir
                else:
                    self.log_signal.emit(f"  [INFO] Using optimized images from 'optimized' subfolder")

                prompt_path = project_dir / self.PROMPT_FILENAME
                prompts_data = self.parse_markdown_prompts(prompt_path)
                
                if not prompts_data:
                    self.log_signal.emit(f"Skipping '{project_dir.name}': Prompts missing.")
                    continue
                
                images = [f for f in image_source_dir.iterdir() if f.suffix.lower() in valid_exts]
                
                # Setup Output Directory (Always use original project name)
                project_out = self.output_path / project_dir.name
                project_out.mkdir(parents=True, exist_ok=True)

                for img_path in images:
                    if self.stop_requested: break
                    
                    # Output subfolder for this specific image
                    image_out_dir = project_out / img_path.stem.replace("_optimized", "")
                    image_out_dir.mkdir(exist_ok=True)
                    
                    current_ratio = self.get_smart_ratio(img_path)
                    img_data = img_path.read_bytes()

                    for data in prompts_data:
                        if self.stop_requested: break
                        self.log_signal.emit(f"  [{project_dir.name}] {img_path.name} -> {data['title']}")
                        
                        try:
                            # Dynamic MIME type detection
                            mime_map = {
                                '.png': 'image/png',
                                '.jpg': 'image/jpeg',
                                '.jpeg': 'image/jpeg',
                                '.webp': 'image/webp'
                            }
                            detected_mime = mime_map.get(img_path.suffix.lower(), 'image/png')

                            # Prepare config with Dynamic Aspect Ratio and Resolution
                            # 2. Handle Aspect Ratio (Bucket-Perfect Detection)
                            # 2. Handle Aspect Ratio
                            # Auto (Native) -> Omitted (Model decides)
                            # Manual -> Calculated from image (Smart)
                            image_config_params = {"image_size": self.resolution}
                            
                            if self.ratio == "Manual":
                                smart_ratio = self.get_smart_ratio(img_path)
                                image_config_params["aspect_ratio"] = smart_ratio
                                self.log_signal.emit(f"    [INFO] Manual Smart Ratio: {smart_ratio}")

                            # 3. Build Config using Official Google AI Studio structure
                            gen_config = types.GenerateContentConfig(
                                response_modalities=["IMAGE", "TEXT"],
                                image_config=types.ImageConfig(**image_config_params),
                                temperature=0.4
                            )

                            # Use types.Content for formal structure
                            contents = [
                                types.Content(
                                    role="user",
                                    parts=[
                                        types.Part.from_text(text=data['prompt']),
                                        types.Part.from_bytes(data=img_data, mime_type=detected_mime)
                                    ]
                                )
                            ]

                            response = client.models.generate_content(
                                model=self.model_id,
                                contents=contents,
                                config=gen_config
                            )
                            
                            if response.parts:
                                for part in response.parts:
                                    if part.inline_data:
                                        ts = datetime.datetime.now().strftime("%H%M%S")
                                        base_name = f"{img_path.stem}_{data['title']}_{ts}"
                                        out_file_path = image_out_dir / f"{base_name}.png"
                                        out_file_path.write_bytes(part.inline_data.data)
                                        
                                        if self.check_logs:
                                            log_text = f"RATIO: {current_ratio}\nPROMPT:\n{data['prompt']}"
                                            (image_out_dir / f"{base_name}.txt").write_text(log_text, encoding="utf-8")
                                        
                                        self.log_signal.emit(f"    [OK] Saved: {base_name}.png")
                                        
                                        # Emit Preview Signal
                                        self.preview_signal.emit(str(img_path), str(out_file_path), data['prompt'])

                        except Exception as e:
                            self.log_signal.emit(f"    [ERROR] API Call failed for {img_path.name}: {e}")
                            print(f"DEBUG: Failed prompt:\n{data['prompt']}")

            if self.stop_requested:
                self.log_signal.emit("--- PROCESS STOPPED BY USER ---")
            else:
                self.log_signal.emit("--- BATCH PROCESS COMPLETED ---")
                self.progress_signal.emit(100)

        except Exception as e:
            self.error_signal.emit(str(e))
        
        self.finished_signal.emit()

    def request_stop(self):
        self.stop_requested = True

    def get_smart_ratio(self, image_path):
        with Image.open(image_path) as img:
            w, h = img.size
            target = w / h
            # Official Imagen 3 / Gemini Ratios
            common = [
                (1, 1), (16, 9), (9, 16), (4, 3), (3, 4), 
                (3, 2), (2, 3), (5, 4), (4, 5), (21, 9)
            ]
            best = min(common, key=lambda r: abs(target - r[0]/r[1]))
            return f"{best[0]}:{best[1]}"

    def parse_markdown_prompts(self, file_path):
        p = Path(file_path)
        if not p.exists(): return []
        content = p.read_text(encoding="utf-8")
        sections = re.split(r'\n###\s+', content)
        parsed = []
        for section in sections[1:]:
            lines = section.strip().split('\n')
            title = re.sub(r'[\\/*?:"<>|]', "", lines[0].strip().replace(" ", "_"))
            body = "\n".join(lines[1:]).strip()
            if body: parsed.append({"title": title, "prompt": body})
        return parsed


class TabBatch(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.MODEL_ID = "gemini-3-pro-image-preview"
        # Empirically Verified Resolution Table (Truth Table)
        self.MODEL_ID = "gemini-3-pro-image-preview"
        self.scan_results = None  # Store scan results for optimization
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)

        # --- LEFT PANEL (Controls) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 1. Config
        # 1. Config Block Removed (Now in Settings)
        
        # 1.5 Grid Validator
        grp_validator = QGroupBox("📋 Image Grid Validator (64px)")
        layout_validator = QVBoxLayout()
        
        # Scan button
        self.btn_scan = QPushButton("🔍 ANALYZE FOR OPTIMIZATION")
        self.btn_scan.setMinimumHeight(35)
        self.btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #106ebe; }
        """)
        self.btn_scan.clicked.connect(self.scan_images)
        layout_validator.addWidget(self.btn_scan)
        
        # Report area
        self.validator_report = QTextEdit()
        self.validator_report.setReadOnly(True)
        self.validator_report.setMaximumHeight(120)
        self.validator_report.setStyleSheet("""
            font-family: Consolas;
            font-size: 11px;
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #3d3d3d;
        """)
        self.validator_report.setPlaceholderText("Click 'SCAN IMAGES' to check grid alignment...")
        layout_validator.addWidget(self.validator_report)
        
        # Optimization button
        self.btn_crop = QPushButton("🍌 OPTIMIZE FOR NANO BANANA PRO")
        self.btn_crop.setMinimumHeight(35)
        self.btn_crop.setStyleSheet("""
            QPushButton {
                background-color: #2da44e;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2c974b; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.btn_crop.clicked.connect(self.auto_crop_images)
        self.btn_crop.setEnabled(False)
        layout_validator.addWidget(self.btn_crop)
        
        grp_validator.setLayout(layout_validator)
        left_layout.addWidget(grp_validator)
        
        # 2. Paths
        grp_paths = QGroupBox("Paths & Settings")
        layout_paths = QGridLayout()

        layout_paths.addWidget(QLabel("Input Root:"), 0, 0)
        self.entry_in = DragDropLineEdit()
        self.entry_in.setPlaceholderText("Drag folder here...")
        self.add_context_menu(self.entry_in)
        layout_paths.addWidget(self.entry_in, 0, 1)
        btn_in = QPushButton("Browse")
        btn_in.clicked.connect(lambda: self.select_path(self.entry_in))
        layout_paths.addWidget(btn_in, 0, 2)

        layout_paths.addWidget(QLabel("Output Folder:"), 1, 0)
        self.entry_out = DragDropLineEdit()
        self.add_context_menu(self.entry_out)
        layout_paths.addWidget(self.entry_out, 1, 1)
        btn_out = QPushButton("Browse")
        btn_out.clicked.connect(lambda: self.select_path(self.entry_out))
        layout_paths.addWidget(btn_out, 1, 2)

        # Settings
        hbox_settings = QHBoxLayout()
        hbox_settings.addWidget(QLabel("Res:"))
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1K", "2K", "4K"])
        self.combo_res.setFixedWidth(70)
        hbox_settings.addWidget(self.combo_res)
        
        hbox_settings.addWidget(QLabel("  Ratio:"))
        self.combo_ratio = QComboBox()
        self.combo_ratio.addItems(["Auto", "Manual"])
        self.combo_ratio.setFixedWidth(100)
        hbox_settings.addWidget(self.combo_ratio)
        
        self.check_logs = QCheckBox("Logs")
        self.check_logs.setChecked(True)
        hbox_settings.addWidget(self.check_logs)
        hbox_settings.addStretch()
        
        layout_paths.addLayout(hbox_settings, 2, 1, 1, 2)
        grp_paths.setLayout(layout_paths)
        left_layout.addWidget(grp_paths)

        # 3. Status
        self.progress = QProgressBar()
        self.progress.setValue(0)
        left_layout.addWidget(self.progress)

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setStyleSheet("font-family: Consolas; font-size: 12px;")
        left_layout.addWidget(self.status_box)

        # 4. Buttons
        hbox_btns = QHBoxLayout()
        self.btn_start = QPushButton("START PROCESSING")
        self.btn_start.setMinimumHeight(45)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; /* GitHub/Apple Success Green */
                color: white; 
                font-weight: bold; 
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2c974b; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.btn_start.clicked.connect(self.start_process)
        
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setMinimumHeight(45)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f; /* Material Red 700 */
                color: white; 
                font-weight: bold; 
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c62828; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.btn_stop.clicked.connect(self.stop_process)
        self.btn_stop.setEnabled(False)

        hbox_btns.addWidget(self.btn_start)
        hbox_btns.addWidget(self.btn_stop)
        left_layout.addLayout(hbox_btns)

        # --- RIGHT PANEL (Preview) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        grp_preview = QGroupBox("Live Preview")
        preview_inner = QVBoxLayout()
        
        # Image Area
        img_layout = QHBoxLayout()
        
        # 1. Image Area (Expands)
        img_layout = QHBoxLayout()
        
        self.lbl_input = ResizingLabel("Waiting...")
        self.lbl_output = ResizingLabel("Waiting...")
        
        lbl_arrow = QLabel("➡")
        lbl_arrow.setAlignment(Qt.AlignCenter)
        lbl_arrow.setStyleSheet("font-size: 20px; font-weight: bold; color: #666;")
        lbl_arrow.setFixedWidth(30)
        
        img_layout.addWidget(self.lbl_input)
        img_layout.addWidget(lbl_arrow, 0, Qt.AlignVCenter)
        img_layout.addWidget(self.lbl_output)
        
        preview_inner.addLayout(img_layout, 3) # Images take 60% height

        # 2. Prompt Area (Fixed at bottom)
        prompt_container = QWidget()
        prompt_layout = QVBoxLayout(prompt_container)
        prompt_layout.setContentsMargins(0, 10, 0, 0)
        prompt_layout.setSpacing(2)

        lbl_prompt = QLabel("Current Prompt:")
        lbl_prompt.setStyleSheet("color: #888; font-size: 11px; font-weight: bold;")
        prompt_layout.addWidget(lbl_prompt)

        self.txt_prompt = QTextEdit()
        self.txt_prompt.setReadOnly(True)
        # self.txt_prompt.setMaximumHeight(70) # Removed limitation
        self.txt_prompt.setStyleSheet("background-color: #2b2b2b; color: #ccc; font-style: italic; border: 1px solid #3d3d3d; border-radius: 4px; padding: 4px;")
        prompt_layout.addWidget(self.txt_prompt)
        
        preview_inner.addWidget(prompt_container, 2) # Prompt takes 40% height
        
        grp_preview.setLayout(preview_inner)
        right_layout.addWidget(grp_preview)

        # --- COMBINE ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        
        # Main layout wrapper to allow splitter to expand
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(splitter)

    def add_context_menu(self, widget):
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(lambda pos: self.show_menu(widget, pos))

    def show_menu(self, widget, pos):
        menu = QMenu(self)
        menu.addAction("Cut", widget.cut)
        menu.addAction("Copy", widget.copy)
        menu.addAction("Paste", widget.paste)
        menu.exec(widget.mapToGlobal(pos))

    def select_path(self, entry):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            entry.setText(path)
            self.save_settings()

    def save_settings(self):
        # config_helper.set_value("api_key", ...) # Handled in Settings Tab now
        config_helper.set_value("input_path", self.entry_in.text().strip())
        config_helper.set_value("output_path", self.entry_out.text().strip())
        config_helper.set_value("resolution", self.combo_res.currentText())
        config_helper.set_value("aspect_ratio", self.combo_ratio.currentText())
        config_helper.set_value("generate_logs", self.check_logs.isChecked())

    def load_settings(self):
        config = config_helper.load_config()
        # self.entry_key.setText(...) # Handled in Settings Tab now
        self.entry_in.setText(config.get("input_path", ""))
        self.entry_out.setText(config.get("output_path", ""))
        self.combo_res.setCurrentText(config.get("resolution", "1K"))
        self.combo_ratio.setCurrentText(config.get("aspect_ratio", "Auto"))
        self.check_logs.setChecked(config.get("generate_logs", True))

    def start_process(self):
        # Read API Key via helper (handles keyring)
        key = config_helper.get_value("api_key", "")
        in_path = self.entry_in.text().strip()
        
        if not key or not in_path:
            self.status_box.append("[ERROR] Invalid API Key (check Settings tab) or Input Path")
            return

        self.save_settings()
        self.status_box.clear()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setValue(0)
        
        self.lbl_input.clear(); self.lbl_input.setText("Processing...")
        self.lbl_output.clear(); self.lbl_output.setText("Waiting...")
        self.txt_prompt.clear()

        # Create and start worker
        self.worker = BatchWorker(
            key, in_path, self.entry_out.text().strip(),
            self.combo_res.currentText(), self.combo_ratio.currentText(),
            self.MODEL_ID, self.check_logs.isChecked(),
            parent=self
        )
        self.worker.log_signal.connect(self.status_box.append)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error_signal.connect(lambda e: self.status_box.append(f"CRITICAL ERROR: {e}"))
        self.worker.preview_signal.connect(self.update_preview)
        
        self.worker.start()

    def stop_process(self):
        if self.worker:
            self.status_box.append("!!! STOP REQUESTED. Finishing current task... !!!")
            self.worker.request_stop()
            self.btn_stop.setEnabled(False)

    def on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.worker = None

    def update_preview(self, in_path, out_path, prompt):
        self.txt_prompt.setText(prompt)
        
        if Path(in_path).exists():
            self.lbl_input.setPixmap(QPixmap(in_path))
        
        if Path(out_path).exists():
            self.lbl_output.setPixmap(QPixmap(out_path))

    def scan_images(self):
        """Scan images in input folder for 64px grid alignment"""
        input_path = self.entry_in.text().strip()
        
        if not input_path or not Path(input_path).exists():
            self.validator_report.setText("❌ ERROR: Please select a valid input folder first!")
            return
        
        input_dir = Path(input_path)
        valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
        
        # Mapping to closest resolution buckets
        optimized_plan = []
        target_quality = self.combo_res.currentText()

        for img_file in input_dir.iterdir():
            if img_file.suffix.lower() in valid_exts:
                try:
                    with Image.open(img_file) as img:
                        w, h = img.size
                        curr_ratio = w / h
                        
                        # Find closest bucket ratio
                        def parse_ratio(r_str):
                            p = r_str.split(':')
                            return int(p[0]) / int(p[1])
                        
                        best_ratio_key = min(RESOLUTION_TABLE.keys(), key=lambda r: abs(curr_ratio - parse_ratio(r)))
                        target_w, target_h = RESOLUTION_TABLE[best_ratio_key][target_quality]
                        
                        already_optimized = (w == target_w and h == target_h)
                        optimized_plan.append({
                            'name': img_file.name,
                            'current': (w, h),
                            'path': img_file,
                            'target': (target_w, target_h),
                            'ratio': best_ratio_key,
                            'optimized': already_optimized
                        })
                except Exception as e:
                    self.validator_report.append(f"⚠️ Error reading {img_file.name}: {e}")
        
        # Store results
        self.scan_results = {
            'input_dir': input_dir,
            'plan': optimized_plan
        }
        
        # Generate report
        report = "=" * 50 + "\n"
        report += f"📊 OPTIMIZATION REPORT ({target_quality})\n"
        report += "=" * 50 + "\n\n"
        
        needs_work = [p for p in optimized_plan if not p['optimized']]
        is_ready = [p for p in optimized_plan if p['optimized']]
        
        report += f"Total Images: {len(optimized_plan)}\n"
        report += f"✅ Perfect: {len(is_ready)}\n"
        report += f"⚙️ To Optimize: {len(needs_work)}\n\n"
        
        if needs_work:
            report += "⚙️ PENDING OPTIMIZATIONS:\n"
            for p in needs_work[:10]:
                report += f"  • {p['name']}: {p['current'][0]}×{p['current'][1]} → {p['target'][0]}×{p['target'][1]} ({p['ratio']})\n"
            if len(needs_work) > 10:
                report += f"  ... and {len(needs_work) - 10} more\n"
            report += "\n"
        
        if is_ready:
            report += "✅ ALREADY OPTIMIZED:\n"
            for p in is_ready[:5]:
                report += f"  • {p['name']} ({p['target'][0]}×{p['target'][1]})\n"
        
        report += "=" * 50 + "\n"
        if needs_work:
            report += "💡 Click 'OPTIMIZE FOR NANO BANANA PRO' to prepare images\n"
        else:
            report += "✅ All images are bucket-perfect!\n"
        
        self.validator_report.setText(report)
        self.btn_crop.setEnabled(len(optimized_plan) > 0)

    def auto_crop_images(self):
        """Optimize images to official Imagen buckets via Aspect Fill + Center Crop"""
        if not self.scan_results:
            self.validator_report.setText("❌ ERROR: Please analyze images first!")
            return
        
        input_dir = self.scan_results['input_dir']
        plan = self.scan_results['plan']
        
        # Create optimized folder
        cropped_dir = input_dir / "optimized"
        cropped_dir.mkdir(exist_ok=True)
        
        self.validator_report.append("\n" + "=" * 50)
        self.validator_report.append(f"🚀 OPTIMIZING FOR BATCH AI...")
        
        processed = 0
        errors = 0
        
        for p in plan:
            if p['optimized']: continue
            try:
                with Image.open(p['path']) as img:
                    # Smart Optimization: Scale to fill -> Center Crop (ImageOps.fit does this perfectly)
                    # This ensures that if aspect ratio is already correct, no cropping happens (just resize)
                    # And if not, it crops evenly from center.
                    target_w, target_h = p['target']
                    
                    # Convert to RGB to avoid issues with RGBA/P modes during complex resizing if needed
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    # ImageOps.fit implements "Scale then Crop" logic
                    new_img = ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    
                    save_path = cropped_dir / f"{p['name'].rsplit('.', 1)[0]}_optimized.{p['name'].split('.')[-1]}"
                    # Save with high quality
                    new_img.save(save_path, quality=95, subsampling=0)
                
                self.validator_report.append(f"✨ Optimized: {p['name']} → {p['target'][0]}×{p['target'][1]} ({p['ratio']})")
                processed += 1
            except Exception as e:
                self.validator_report.append(f"❌ Error optimizing {p['name']}: {e}")
                errors += 1
        
        # Final report
        self.validator_report.append("\n" + "=" * 50)
        self.validator_report.append(f"✅ OPTIMIZATION COMPLETE!")
        self.validator_report.append(f"Processed: {processed} | Errors: {errors}")
        self.validator_report.append(f"Output: {cropped_dir}")
        self.validator_report.append("=" * 50)
        
        self.validator_report.append("\n💡 Optimized images are ready and will be used as high-quality inputs.")
