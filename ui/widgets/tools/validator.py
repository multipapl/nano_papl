from pathlib import Path
from PIL import Image, ImageOps
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import TextEdit, BodyLabel, PrimaryPushButton, PushButton, FluentIcon
from ui.components import SectionCard, ModernPathSelector, NPButton
from core.config.resolutions import RESOLUTION_TABLE
from core import constants

class ValidatorWidget(QWidget):
    """
    Image Grid Validator component for the Tools page.
    Handles scanning and optimizing image alignments.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scan_results = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        self.card = SectionCard("Image Grid Validator", FluentIcon.CHECKBOX)
        
        # Path Selector
        self.path_input = ModernPathSelector("Input Directory:", select_file=False)
        self.path_input.setToolTip("Select the directory containing project folders or raw images to validate.")
        self.card.addWidget(self.path_input)

        # Actions
        h_val = QHBoxLayout()
        h_val.setSpacing(10)
        
        self.btn_scan = NPButton("ANALYZE", FluentIcon.SEARCH)
        self.btn_scan.clicked.connect(self.scan_images)
        self.btn_scan.setToolTip("Analyze selected directory for image alignment and resolution issues.")
        h_val.addWidget(self.btn_scan)
        
        self.btn_crop = NPButton("OPTIMIZE", FluentIcon.PHOTO, is_primary=False)
        self.btn_crop.clicked.connect(self.auto_crop_images)
        self.btn_crop.setEnabled(False)
        self.btn_crop.setToolTip("Automatically fit and crop images to the nearest standard resolution and aspect ratio.")
        h_val.addWidget(self.btn_crop)
        
        h_val.addStretch()
        self.card.addLayout(h_val)
        
        # Report Area
        self.validator_report = TextEdit()
        self.validator_report.setReadOnly(True)
        self.validator_report.setFixedHeight(100)
        self.validator_report.setPlaceholderText("Select a folder and click Analyze to check alignment...")
        self.validator_report.setToolTip("Detailed report of the analysis and optimization results.")
        self.card.addWidget(self.validator_report)
        
        layout.addWidget(self.card)

    def scan_images(self):
        input_path = self.path_input.get_path()
        if not input_path or not Path(input_path).exists():
            self.validator_report.setText("❌ Select valid input folder!")
            return
        
        input_dir = Path(input_path)
        valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
        
        projects = []
        if (input_dir / constants.DEFAULT_PROMPTS_FILE).exists():
            projects = [input_dir]
        else:
            projects = [d for d in input_dir.iterdir() if d.is_dir()]
        
        if not projects:
             self.validator_report.setText("⚠️ No project folders found.")
             return

        optimized_plan = []
        
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
                            available_resolutions = RESOLUTION_TABLE[best_ratio]
                            original_area = w * h
                            
                            best_quality = None
                            min_diff = float('inf')
                            
                            for q_name, (rw, rh) in available_resolutions.items():
                                r_area = rw * rh
                                diff = abs(original_area - r_area)
                                if diff < min_diff:
                                    min_diff = diff
                                    best_quality = q_name
                            
                            target = available_resolutions[best_quality]
                            
                            optimized_plan.append({
                                'name': img_file.name,
                                'path': img_file,
                                'project_dir': project_dir,
                                'target': target,
                                'target_quality': best_quality,
                                'ratio': best_ratio,
                                'optimized': (w == target[0] and h == target[1])
                            })
                    except: pass
        
        self.scan_results = {'input_dir': input_dir, 'plan': optimized_plan}
        
        ready = len([p for p in optimized_plan if p['optimized']])
        total = len(optimized_plan)
        report = f"📊 REPORT (Auto-Resolution)\nTotal: {total} | Ready: {ready} | Needs Opt: {total - ready}\n"
        
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
                    out_dir = p_dir / constants.OPTIMIZED_DIR_NAME
                    out_dir.mkdir(exist_ok=True)
                    
                    save_name = f"{p['name'].rsplit('.', 1)[0]}_optimized.{p['name'].split('.')[-1]}"
                    new_img.save(out_dir / save_name, quality=95)
                    processed += 1
            except: pass
            
        self.validator_report.append(f"✅ DONE! Optimized {processed} images.")
        self.scan_results = None
        self.btn_crop.setEnabled(False)
