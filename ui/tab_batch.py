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
from PIL import Image
from google import genai
from google.genai import types
from utils import config_helper

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

    def __init__(self, api_key, input_path, output_path, resolution, model_id, check_logs, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else self.input_path / "_renders"
        self.resolution = resolution
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

                prompt_path = project_dir / self.PROMPT_FILENAME
                prompts_data = self.parse_markdown_prompts(prompt_path)
                
                if not prompts_data:
                    self.log_signal.emit(f"Skipping '{project_dir.name}': Prompts missing.")
                    continue
                
                images = [f for f in project_dir.iterdir() if f.suffix.lower() in valid_exts]
                
                # Setup Output Directory
                project_out = self.output_path / project_dir.name
                project_out.mkdir(parents=True, exist_ok=True)

                for img_path in images:
                    if self.stop_requested: break
                    current_ratio = self.get_smart_ratio(img_path)
                    img_data = img_path.read_bytes()

                    for data in prompts_data:
                        if self.stop_requested: break
                        self.log_signal.emit(f"  [{project_dir.name}] {img_path.name} -> {data['title']}")
                        
                        try:
                            response = client.models.generate_content(
                                model=self.model_id,
                                contents=[
                                    data['prompt'],
                                    types.Part.from_bytes(data=img_data, mime_type="image/png")
                                ],
                                config=types.GenerateContentConfig(
                                    response_modalities=["IMAGE"],
                                )
                            )
                            
                            if response.parts:
                                for part in response.parts:
                                    if part.inline_data:
                                        ts = datetime.datetime.now().strftime("%H%M%S")
                                        base_name = f"{img_path.stem}_{data['title']}_{ts}"
                                        out_file_path = project_out / f"{base_name}.png"
                                        out_file_path.write_bytes(part.inline_data.data)
                                        
                                        if self.check_logs:
                                            log_text = f"RATIO: {current_ratio}\nPROMPT:\n{data['prompt']}"
                                            (project_out / f"{base_name}.txt").write_text(log_text, encoding="utf-8")
                                        
                                        self.log_signal.emit(f"    [OK] Saved: {base_name}.png")
                                        
                                        # Emit Preview Signal
                                        self.preview_signal.emit(str(img_path), str(out_file_path), data['prompt'])

                        except Exception as e:
                            self.log_signal.emit(f"    [ERROR] API Call failed: {e}")

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
            gcd = math.gcd(w, h)
            rw, rh = w // gcd, h // gcd
            if rw > 50 or rh > 50:
                target = w / h
                common = [(1,1), (16,9), (9,16), (4,3), (3,4), (21,9), (3,2), (2,3)]
                best = min(common, key=lambda r: abs(target - r[0]/r[1]))
                return f"{best[0]}:{best[1]}"
            return f"{rw}:{rh}"

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
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)

        # --- LEFT PANEL (Controls) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 1. Config
        # 1. Config Block Removed (Now in Settings)
        
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
        hbox_settings.addWidget(QLabel("Resolution:"))
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1K", "2K", "4K"])
        hbox_settings.addWidget(self.combo_res)
        
        self.check_logs = QCheckBox("Save Metadata Logs (.txt)")
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
        config_helper.set_value("generate_logs", self.check_logs.isChecked())

    def load_settings(self):
        config = config_helper.load_config()
        # self.entry_key.setText(...) # Handled in Settings Tab now
        self.entry_in.setText(config.get("input_path", ""))
        self.entry_out.setText(config.get("output_path", ""))
        self.combo_res.setCurrentText(config.get("resolution", "1K"))
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
            self.combo_res.currentText(), self.MODEL_ID, self.check_logs.isChecked(),
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
