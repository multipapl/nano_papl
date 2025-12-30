from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QScrollArea, QCheckBox, QComboBox, QGroupBox, QFileDialog, QTextEdit
)
from PySide6.QtCore import Qt
from pathlib import Path
from core.generator import PromptGenerator
from utils import config_helper

class TabConstructor(QWidget):
    def __init__(self):
        super().__init__()
        
        self.generator = PromptGenerator()
        self.data = self.generator.get_template_data()
        
        # Main Layout
        main_layout = QVBoxLayout(self)
        
        # Reset Button Bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        btn_reset = QPushButton("Reset All Defaults")
        btn_reset.setStyleSheet("background-color: #d32f2f; color: white; border-radius: 4px; padding: 5px 10px;")
        btn_reset.clicked.connect(self.global_reset)
        top_bar.addWidget(btn_reset)
        main_layout.addLayout(top_bar)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        
        self._setup_ui()
        self.load_state()

        # content_layout_wrapper = QVBoxLayout(content_widget) # REMOVED: Redundant
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Generate Button
        self.btn_gen = QPushButton("GENERATE PROMPTS MATRIX")
        self.btn_gen.setMinimumHeight(45)
        self.btn_gen.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; /* GitHub/Apple Success Green */
                color: white; 
                font-weight: bold; 
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2c974b; }
        """)
        self.btn_gen.clicked.connect(self.generate)
        main_layout.addWidget(self.btn_gen)

    def _setup_ui(self):
        # --- Project Details ---
        grp_proj = QGroupBox("Project Details")
        l_proj = QVBoxLayout()
        
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Project Name:"))
        self.entry_name = QLineEdit("New_Project")
        h1.addWidget(self.entry_name)
        l_proj.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Context/Loc:"))
        self.entry_ctx = QLineEdit()
        h2.addWidget(self.entry_ctx)
        l_proj.addLayout(h2)
        
        grp_proj.setLayout(l_proj)
        self.content_layout.addWidget(grp_proj)

        # --- Scene Configuration ---
        grp_scene = QGroupBox("Scene Configuration")
        l_scene = QVBoxLayout()
        
        h_sel = QHBoxLayout()
        self.combo_type = QComboBox()
        self.combo_type.addItems(list(self.data.get("input_types", {}).keys()))
        self.combo_type.currentTextChanged.connect(self.update_base_text)
        
        self.combo_cat = QComboBox()
        self.combo_cat.addItems(list(self.data.get("scene_types", {}).keys()))
        self.combo_cat.currentTextChanged.connect(self.update_base_text)
        
        h_sel.addWidget(self.combo_type)
        h_sel.addWidget(self.combo_cat)
        l_scene.addLayout(h_sel)

        self.text_base = QTextEdit()
        self.text_base.setMaximumHeight(80)
        l_scene.addWidget(self.text_base)
        
        grp_scene.setLayout(l_scene)
        self.content_layout.addWidget(grp_scene)

        # --- Seasons ---
        grp_seasons = QGroupBox("Seasons & Atmosphere")
        l_seasons = QVBoxLayout()
        self.season_rows = {}
        
        for s_name, s_desc in self.data.get("seasons", {}).items():
            row = QHBoxLayout()
            chk = QCheckBox(s_name)
            chk.setFixedWidth(100)
            
            e_desc = QLineEdit(s_desc)
            self.create_reset_btn(e_desc, "seasons", s_name, row)
            
            e_atmos = QLineEdit(self.data.get("default_atmospheres", {}).get(s_name, ""))
            self.create_reset_btn(e_atmos, "default_atmospheres", s_name, row)

            row.insertWidget(0, chk)
            row.insertWidget(2, e_desc)
            row.insertWidget(4, e_atmos)
            
            l_seasons.addLayout(row)
            self.season_rows[s_name] = {"chk": chk, "desc": e_desc, "atmos": e_atmos}
            
        grp_seasons.setLayout(l_seasons)
        self.content_layout.addWidget(grp_seasons)

        # --- Lighting ---
        grp_light = QGroupBox("Lighting Scenarios")
        l_light = QVBoxLayout()
        self.light_rows = {}
        
        for l_name, l_desc in self.data.get("lighting", {}).items():
            row = QHBoxLayout()
            chk = QCheckBox(l_name)
            chk.setChecked(True)
            chk.setFixedWidth(120)
            
            chk_xmas = QCheckBox("Xmas")
            chk_xmas.setStyleSheet("color: #e74c3c")
            
            e_desc = QLineEdit(l_desc)
            self.create_reset_btn(e_desc, "lighting", l_name, row)
            
            row.insertWidget(0, chk)
            row.insertWidget(1, chk_xmas)
            row.insertWidget(3, e_desc)
            
            l_light.addLayout(row)
            self.light_rows[l_name] = {"chk": chk, "xmas": chk_xmas, "desc": e_desc}
            
        grp_light.setLayout(l_light)
        self.content_layout.addWidget(grp_light)

        # --- Global Settings ---
        grp_global = QGroupBox("Global Settings")
        l_global = QVBoxLayout()
        
        self.entry_xmas = self.create_setting_row("Xmas Desc:", "christmas_desc", l_global)
        self.entry_rules = self.create_setting_row("Global Rules:", "global_rules", l_global)
        self.entry_cam = self.create_setting_row("Camera:", "camera", l_global)
        
        grp_global.setLayout(l_global)
        self.content_layout.addWidget(grp_global)

        self.update_base_text()

    def create_reset_btn(self, target, key, subkey, layout):
        btn = QPushButton("R")
        btn.setFixedWidth(25)
        btn.clicked.connect(lambda: self.reset_field(target, key, subkey))
        layout.addWidget(btn)

    def reset_field(self, target, key, subkey=None):
        val = ""
        if subkey:
            val = self.data.get(key, {}).get(subkey, "")
        else:
            val = self.data.get(key, "")
        target.setText(val)

    def create_setting_row(self, label, key, parent_layout):
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        entry = QLineEdit()
        self.create_reset_btn(entry, key, None, row)
        row.insertWidget(1, entry)
        parent_layout.addLayout(row)
        return entry

    def update_base_text(self, *args):
        t = self.data.get("input_types", {}).get(self.combo_type.currentText(), "")
        c = self.data.get("scene_types", {}).get(self.combo_cat.currentText(), "")
        self.text_base.setText(f"{t} {c}")

    def get_current_settings(self):
        return {
            "project_name": self.entry_name.text(),
            "context": self.entry_ctx.text(),
            "input_type": self.combo_type.currentText(),
            "scene_type": self.combo_cat.currentText(),
            "base_text": self.text_base.toPlainText().strip(),
            "xmas_desc": self.entry_xmas.text(),
            "global_rules": self.entry_rules.text(),
            "camera": self.entry_cam.text(),
            "active_seasons": {
                n: {
                    "is_active": r["chk"].isChecked(),
                    "season_text": r["desc"].text(),
                    "atmos": r["atmos"].text()
                } for n, r in self.season_rows.items()
            },
            "active_lights": {
                n: {
                    "is_active": r["chk"].isChecked(),
                    "desc": r["desc"].text(),
                    "is_xmas": r["xmas"].isChecked()
                } for n, r in self.light_rows.items()
            }
        }

    def save_state(self):
        settings = self.get_current_settings()
        full_config = config_helper.load_config()
        full_config.update({
            "constructor_project_name": settings["project_name"],
            "constructor_context": settings["context"],
            "constructor_input_type": settings["input_type"],
            "constructor_scene_type": settings["scene_type"],
            "constructor_xmas_desc": settings["xmas_desc"],
            "constructor_global_rules": settings["global_rules"],
            "constructor_camera": settings["camera"],
            "constructor_seasons": settings["active_seasons"],
            "constructor_lights": settings["active_lights"]
        })
        config_helper.save_config(full_config)

    def load_state(self):
        config = config_helper.load_config()
        self.entry_name.setText(config.get("constructor_project_name", "New_Project"))
        self.entry_ctx.setText(config.get("constructor_context", "New Zeeland"))
        self.combo_type.setCurrentText(config.get("constructor_input_type", "Viewport"))
        self.combo_cat.setCurrentText(config.get("constructor_scene_type", "Exterior"))
        
        self.entry_xmas.setText(config.get("constructor_xmas_desc", ""))
        self.entry_rules.setText(config.get("constructor_global_rules", ""))
        self.entry_cam.setText(config.get("constructor_camera", ""))
        
        saved_seasons = config.get("constructor_seasons", {})
        for n, r in self.season_rows.items():
            if n in saved_seasons:
                s_data = saved_seasons[n]
                r["chk"].setChecked(s_data.get("is_active", False))
                r["desc"].setText(s_data.get("season_text", ""))
                r["atmos"].setText(s_data.get("atmos", ""))
        
        saved_lights = config.get("constructor_lights", {})
        for n, r in self.light_rows.items():
            if n in saved_lights:
                l_data = saved_lights[n]
                r["chk"].setChecked(l_data.get("is_active", True))
                r["desc"].setText(l_data.get("desc", ""))
                r["xmas"].setChecked(l_data.get("is_xmas", False))
        
        self.update_base_text()

    def global_reset(self):
        # Implementation similar to previous logic but setting Qt widgets
        self.entry_name.setText("New_Project")
        self.entry_ctx.setText("New Zeeland")
        self.entry_xmas.setText(self.data.get("christmas_desc", ""))
        self.entry_rules.setText(self.data.get("global_rules", ""))
        self.entry_cam.setText(self.data.get("camera", ""))
        
        for name, row in self.season_rows.items():
            row["chk"].setChecked(False)
            row["desc"].setText(self.data.get("seasons", {}).get(name, ""))
            row["atmos"].setText(self.data.get("default_atmospheres", {}).get(name, ""))
            
        for name, row in self.light_rows.items():
            row["chk"].setChecked(True)
            row["xmas"].setChecked(False)
            row["desc"].setText(self.data.get("lighting", {}).get(name, ""))
            
        self.update_base_text()
        self.save_state()

    def generate(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not folder: return
        self.save_state()
        
        try:
            settings = self.get_current_settings()
            content = self.generator.generate_markdown(settings)
            
            out_file = Path(folder) / "prompts.md"
            out_file.write_text(content, encoding="utf-8")
            
            self.btn_gen.setText("SUCCESS!")
            # In Qt we use QTimer for delayed actions on UI
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.btn_gen.setText("GENERATE PROMPTS MATRIX"))
            
        except Exception as e:
            self.btn_gen.setText(f"ERROR: {e}")
