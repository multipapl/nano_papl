import os
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    ComboBox, BodyLabel, CaptionLabel, 
    StrongBodyLabel, LineEdit, SpinBox, CheckBox, TextEdit
)
from core.utils import config_helper
from ui.components import ModernPathSelector, SectionCard

class ConfigPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._init_ui()
        
    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 10, 20, 20)
        self.layout.setSpacing(15)
        
        # 1. Project Paths
        paths_card = SectionCard("Project Paths")
        self.path_in = ModernPathSelector("Input Root:", "", select_file=False)
        self.path_out = ModernPathSelector("Output Folder:", "", select_file=False)
        paths_card.addWidget(self.path_in)
        paths_card.addWidget(self.path_out)
        self.layout.addWidget(paths_card)
        
        # 2. Generation Settings
        settings_card = SectionCard("Generation Settings")
        
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(BodyLabel("Engine:"))
        self.combo_engine = ComboBox()
        self.combo_engine.addItems(["Google Gemini (API)", "ComfyUI (Local)"])
        self.combo_engine.currentTextChanged.connect(self._on_engine_changed)
        engine_layout.addWidget(self.combo_engine, 1)
        settings_card.addLayout(engine_layout)
        
        params_layout = QHBoxLayout()
        v_res = QVBoxLayout()
        v_res.addWidget(CaptionLabel("Resolution"))
        self.combo_res = ComboBox()
        self.combo_res.addItems(["1K", "2K", "4K"])
        v_res.addWidget(self.combo_res)
        params_layout.addLayout(v_res, 1)
        
        v_ratio = QVBoxLayout()
        v_ratio.addWidget(CaptionLabel("Aspect Ratio"))
        self.combo_ratio = ComboBox()
        self.combo_ratio.addItems(["Auto", "1:1", "16:9", "9:16", "4:5", "3:4"])
        v_ratio.addWidget(self.combo_ratio)
        params_layout.addLayout(v_ratio, 1)
        settings_card.addLayout(params_layout)
        
        self.check_save_logs = CheckBox("Save individual .txt logs")
        self.check_save_logs.setChecked(True)
        settings_card.addWidget(self.check_save_logs)
        
        self.layout.addWidget(settings_card)
        
        # 3. Google Parameters
        self.google_card = SectionCard("Google Parameters")
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(BodyLabel("Format:"))
        self.combo_fmt = ComboBox()
        self.combo_fmt.addItems(["PNG", "JPG"])
        fmt_layout.addWidget(self.combo_fmt, 1)
        self.google_card.addLayout(fmt_layout)
        
        self.lbl_api_counter = CaptionLabel("RDP Usage: ...")
        self.google_card.addWidget(self.lbl_api_counter)
        self.layout.addWidget(self.google_card)
        
        # 4. ComfyUI Parameters
        self.comfy_card = SectionCard("ComfyUI Parameters")
        self.comfy_card.setVisible(False)
        
        seed_layout = QHBoxLayout()
        self.check_random_seed = CheckBox("Random Seed")
        self.check_random_seed.setChecked(True)
        self.spin_seed = SpinBox()
        self.spin_seed.setRange(0, 999999999)
        self.spin_seed.setValue(123456789)
        self.spin_seed.setEnabled(False)
        self.check_random_seed.toggled.connect(lambda c: self.spin_seed.setEnabled(not c))
        seed_layout.addWidget(self.check_random_seed)
        seed_layout.addWidget(self.spin_seed, 1)
        self.comfy_card.addLayout(seed_layout)
        
        self.comfy_card.addWidget(CaptionLabel("System Prompt Override"))
        self.text_sys_prompt = TextEdit()
        self.text_sys_prompt.setPlaceholderText("Override workflow default...")
        self.text_sys_prompt.setFixedHeight(80)
        self.comfy_card.addWidget(self.text_sys_prompt)
        
        self.check_dry_run = CheckBox("Dry Run (Upload only)")
        self.comfy_card.addWidget(self.check_dry_run)
        self.layout.addWidget(self.comfy_card)
        
        self.layout.addStretch(1)

    def _on_engine_changed(self, text):
        is_google = "Google" in text
        self.google_card.setVisible(is_google)
        self.comfy_card.setVisible(not is_google)

    def get_state(self):
        return {
            "batch_engine": self.combo_engine.currentIndex(),
            "batch_res": self.combo_res.currentIndex(),
            "batch_ratio": self.combo_ratio.currentIndex(),
            "batch_fmt": self.combo_fmt.currentIndex(),
            "batch_save_logs": self.check_save_logs.isChecked(),
            "batch_seed_val": self.spin_seed.value(),
            "batch_random_seed": self.check_random_seed.isChecked(),
            "batch_input_path": self.path_in.get_path(),
            "batch_output_path": self.path_out.get_path()
        }

    def load_state(self):
        def set_combo(combo, val):
            if isinstance(val, str):
                combo.setCurrentText(val)
            else:
                try: combo.setCurrentIndex(int(val))
                except: pass

        set_combo(self.combo_engine, config_helper.get_value("batch_engine", 0))
        set_combo(self.combo_res, config_helper.get_value("batch_res", 1)) # Default to 2K
        set_combo(self.combo_ratio, config_helper.get_value("batch_ratio", 0))
        set_combo(self.combo_fmt, config_helper.get_value("batch_fmt", 0))
        
        self.check_save_logs.setChecked(bool(config_helper.get_value("batch_save_logs", True)))
        
        try: self.spin_seed.setValue(int(config_helper.get_value("batch_seed_val", 123456789)))
        except: pass
        
        self.check_random_seed.setChecked(bool(config_helper.get_value("batch_random_seed", True)))
        self.path_in.set_path(config_helper.get_value("batch_input_path", ""))
        self.path_out.set_path(config_helper.get_value("batch_output_path", ""))
