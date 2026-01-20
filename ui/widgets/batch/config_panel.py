import os
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    ComboBox, BodyLabel, CaptionLabel, 
    StrongBodyLabel, LineEdit, SpinBox, CheckBox, TextEdit
)
from core.utils import config_helper
from core.config.resolutions import SUPPORTED_ASPECT_RATIOS
from ui.components import ModernPathSelector, SectionCard, GenerationConfigWidget

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
        self.path_in.setToolTip("Select the root directory containing source images for batch processing.")
        self.path_out = ModernPathSelector("Output Folder:", "", select_file=False)
        self.path_out.setToolTip("Select the destination folder where generated images and logs will be saved.")
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
        self.combo_engine.setToolTip("Select the generation engine: Cloud-based Google Gemini or Local ComfyUI instance.")
        engine_layout.addWidget(self.combo_engine, 1)
        settings_card.addLayout(engine_layout)
        
        # Centralized Generation Config Widget
        self.gen_config = GenerationConfigWidget(self)
        settings_card.addWidget(self.gen_config)
        
        self.check_save_logs = CheckBox("Save individual .txt logs")
        self.check_save_logs.setChecked(True)
        self.check_save_logs.setToolTip("If enabled, a .txt file containing the prompt will be saved alongside each image.")
        settings_card.addWidget(self.check_save_logs)
        
        self.layout.addWidget(settings_card)
        
        # 3. Google Parameters
        self.google_card = SectionCard("Google Parameters")
        self.lbl_api_counter = CaptionLabel("RPD Usage: ...")
        self.google_card.addWidget(self.lbl_api_counter)
        self.layout.addWidget(self.google_card)
        
        # 4. ComfyUI Parameters
        self.comfy_card = SectionCard("ComfyUI Parameters")
        self.comfy_card.setVisible(False)
        
        seed_layout = QHBoxLayout()
        self.check_random_seed = CheckBox("Random Seed")
        self.check_random_seed.setChecked(True)
        self.check_random_seed.setToolTip("Use a unique random seed for every image in the batch.")
        self.spin_seed = SpinBox()
        self.spin_seed.setRange(0, 999999999)
        self.spin_seed.setValue(123456789)
        self.spin_seed.setEnabled(False)
        self.spin_seed.setToolTip("Fixed seed value for deterministic generation results.")
        self.check_random_seed.toggled.connect(lambda c: self.spin_seed.setEnabled(not c))
        seed_layout.addWidget(self.check_random_seed)
        seed_layout.addWidget(self.spin_seed, 1)
        self.comfy_card.addLayout(seed_layout)
        
        self.comfy_card.addWidget(CaptionLabel("System Prompt Override"))
        self.text_sys_prompt = TextEdit()
        self.text_sys_prompt.setPlaceholderText("Override workflow default...")
        self.text_sys_prompt.setFixedHeight(80)
        self.text_sys_prompt.setToolTip("Customize the systemic guidance for the AI (works for ComfyUI specifically).")
        self.comfy_card.addWidget(self.text_sys_prompt)
        
        self.check_dry_run = CheckBox("Dry Run (Upload only)")
        self.check_dry_run.setToolTip("Simulate the process: uploads images to the server without starting actual generation.")
        self.comfy_card.addWidget(self.check_dry_run)
        self.layout.addWidget(self.comfy_card)
        
        self.layout.addStretch(1)

    def _on_engine_changed(self, text):
        is_google = "Google" in text
        self.google_card.setVisible(is_google)
        self.comfy_card.setVisible(not is_google)

    def get_state(self):
        state = {
            "batch_engine": self.combo_engine.currentIndex(),
            "batch_save_logs": self.check_save_logs.isChecked(),
            "batch_seed_val": self.spin_seed.value(),
            "batch_random_seed": self.check_random_seed.isChecked(),
            "batch_input_path": self.path_in.get_path(),
            "batch_output_path": self.path_out.get_path()
        }
        # Standardized generation config mapping (preserving legacy keys for compatibility if needed)
        gen_cfg = self.gen_config.get_config()
        state.update({
            "batch_res": gen_cfg["res_index"],
            "batch_ratio": gen_cfg["ratio_index"],
            "batch_fmt": gen_cfg["format_index"]
        })
        return state

    def load_state(self):
        def set_combo(combo, val):
            if isinstance(val, str):
                combo.setCurrentText(val)
            else:
                try: combo.setCurrentIndex(int(val))
                except: pass

        set_combo(self.combo_engine, config_helper.get_value("batch_engine", 0))
        
        # Load centralized generation config
        self.gen_config.set_config({
            "res_index": config_helper.get_value("batch_res", 1),
            "ratio_index": config_helper.get_value("batch_ratio", 0),
            "format_index": config_helper.get_value("batch_fmt", 0)
        })
        
        self.check_save_logs.setChecked(bool(config_helper.get_value("batch_save_logs", True)))
        
        try: self.spin_seed.setValue(int(config_helper.get_value("batch_seed_val", 123456789)))
        except: pass
        
        self.check_random_seed.setChecked(bool(config_helper.get_value("batch_random_seed", True)))
        self.path_in.set_path(config_helper.get_value("batch_input_path", ""))
        self.path_out.set_path(config_helper.get_value("batch_output_path", ""))
