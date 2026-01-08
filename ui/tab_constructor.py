from ui.styles import Styles, Colors
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QScrollArea, QComboBox, QGroupBox, QFileDialog, QTextEdit,
    QMessageBox, QFormLayout, QSizePolicy
)

from PySide6.QtCore import Qt
from core.generator import PromptGenerator
from core.utils import config_helper
from ui.widgets.preset_bar import PresetToolbarWidget
from ui.widgets.seasons_tree import SeasonsTreeWidget
from ui.base_tab import BaseTab
from ui.ui_factory import UIFactory
from pathlib import Path
from core.utils.resource_helper import get_resource_path

class TabConstructor(BaseTab):
    """
    Main workspace for constructing prompts and managing seasons/lighting.
    Handles UI for prompt assembly, history, and sending prompts to Batch/Chat.
    """
    def __init__(self):
        super().__init__()
        
        # Apply Global Styles (Reset)
        self.setStyleSheet(Styles.GLOBAL + Styles.INPUT_FIELD + Styles.BTN_BASE)
        
        self.generator = PromptGenerator()
        self.data = self.generator.get_template_data()
        
        # Main Layout
        main_layout = QVBoxLayout(self)
        
        # --- Presets Toolbar ---
        self.preset_bar = PresetToolbarWidget(
            presets_file=config_helper.PRESETS_FILE,
            show_reset=True,
            reset_label="Reset All Defaults"
        )
        self.preset_bar.preset_loaded.connect(self.apply_preset_data)
        self.preset_bar.save_requested.connect(self.on_save_preset_requested)
        self.preset_bar.reset_requested.connect(self.global_reset)
        main_layout.addWidget(self.preset_bar)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Fix: Ensure transparent background for scroll area content to pick up global style
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }") 
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(20) # Add breathing room between groups
        
        self._setup_ui()
        self._register_fields()  # NEW: Register all stateful fields
        self.load_state()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Generate Button
        self.btn_gen = QPushButton("GENERATE PROMPTS MATRIX")
        self.btn_gen.setMinimumHeight(45)
        self.btn_gen.setStyleSheet(Styles.BTN_PRIMARY)
        self.btn_gen.clicked.connect(self.generate)
        main_layout.addWidget(self.btn_gen)

    def _setup_ui(self):
        # --- Project Details ---
        grp_proj = QGroupBox("Project Details")
        layout_proj = QFormLayout()
        layout_proj.setLabelAlignment(Qt.AlignRight)
        
        self.entry_name = QLineEdit("New_Project")
        layout_proj.addRow("Project Name:", self.entry_name)

        self.entry_ctx = QLineEdit()
        layout_proj.addRow("Context/Loc:", self.entry_ctx)
        
        grp_proj.setLayout(layout_proj)
        self.content_layout.addWidget(grp_proj)

        # --- Scene Configuration ---
        grp_scene = QGroupBox("Scene Configuration")
        layout_scene = QVBoxLayout()
        
        h_sel = QHBoxLayout()
        self.combo_type = QComboBox()
        self.combo_type.addItems(list(self.data.get("input_types", {}).keys()))
        self.combo_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_type.currentTextChanged.connect(self.update_base_text)
        
        self.combo_cat = QComboBox()
        self.combo_cat.addItems(list(self.data.get("scene_types", {}).keys()))
        self.combo_cat.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_cat.currentTextChanged.connect(self.update_base_text)
        
        h_sel.addWidget(self.combo_type)
        h_sel.addWidget(self.combo_cat)
        layout_scene.addLayout(h_sel)

        self.text_base = QTextEdit()
        self.text_base.setMaximumHeight(80)
        self.text_base.setStyleSheet(Styles.TEXT_AREA_CONSOLE)
        layout_scene.addWidget(self.text_base)
        
        grp_scene.setLayout(layout_scene)
        self.content_layout.addWidget(grp_scene)

        # --- Lighting Definitions (Global) ---
        grp_lighting_defs = QGroupBox("Global Lighting Definitions")
        layout_defs = QFormLayout()
        layout_defs.setLabelAlignment(Qt.AlignRight)
        self.light_defs = {} 
        
        default_lights = self.data.get("lighting", {})
        
        for l_name, l_desc in default_lights.items():
            entry = QLineEdit(l_desc)
            # Create a small layout to hold entry + reset button for the Form Row
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0,0,0,0)
            row_layout.setSpacing(5)
            
            row_layout.addWidget(entry)
            
            btn_reset = QPushButton("R")
            btn_reset.setFixedWidth(25)
            btn_reset.setStyleSheet(Styles.BTN_GHOST)
            # Fix lambda capture
            btn_reset.clicked.connect(lambda checked=False, e=entry, k="lighting", sk=l_name: self.reset_field(e, k, sk))
            row_layout.addWidget(btn_reset)
            
            layout_defs.addRow(f"{l_name}:", row_widget)
            self.light_defs[l_name] = entry
            
        grp_lighting_defs.setLayout(layout_defs)
        self.content_layout.addWidget(grp_lighting_defs)

        # --- Seasons & Lighting Hierarchy ---
        grp_tree = QGroupBox("Seasons Lighting Hierarchy")
        l_tree = QVBoxLayout()
        # [MODULARITY] Replaced manual tree with Widget
        self.seasons_widget = SeasonsTreeWidget(self.data)
        l_tree.addWidget(self.seasons_widget)
        grp_tree.setLayout(l_tree)
        self.content_layout.addWidget(grp_tree)

        # --- Global Settings ---
        grp_global = QGroupBox("Global Settings")
        layout_global = QFormLayout()
        layout_global.setLabelAlignment(Qt.AlignRight)
        
        # Use UIFactory instead of create_setting_row_new
        self.entry_xmas = UIFactory.create_input_with_reset(
            reset_value=self.data.get("christmas_desc", ""),
            placeholder="Christmas description..."
        )
        layout_global.addRow("Xmas Desc:", self.entry_xmas)
        
        self.entry_rules = UIFactory.create_input_with_reset(
            reset_value=self.data.get("global_rules", ""),
            placeholder="Global rules..."
        )
        layout_global.addRow("Global Rules:", self.entry_rules)
        
        self.entry_cam = UIFactory.create_input_with_reset(
            reset_value=self.data.get("camera", ""),
            placeholder="Camera settings..."
        )
        layout_global.addRow("Camera:", self.entry_cam)
        
        grp_global.setLayout(layout_global)
        self.content_layout.addWidget(grp_global)

        self.update_base_text()

    def _register_fields(self):
        """
        Register all stateful widgets with the base class field registry.
        This eliminates the need for manual get_current_settings() mapping.
        """
        # Basic fields
        self.register_field("constructor_project_name", self.entry_name)
        self.register_field("constructor_context", self.entry_ctx)
        self.register_field("constructor_input_type", self.combo_type)
        self.register_field("constructor_scene_type", self.combo_cat)
        self.register_field("constructor_xmas_desc", self.entry_xmas)
        self.register_field("constructor_global_rules", self.entry_rules)
        self.register_field("constructor_camera", self.entry_cam)
        
        # Note: seasons_widget and light_defs need special handling in save/load
        # They are handled in overridden save_state/load_state methods
    
    def reset_field(self, target, key, subkey=None):
        """Reset a specific field to its default value"""
        val = ""
        if subkey:
            val = self.data.get(key, {}).get(subkey, "")
        else:
            val = self.data.get(key, "")
        target.setText(val)

    def update_base_text(self, *args):
        t = self.data.get("input_types", {}).get(self.combo_type.currentText(), "")
        c = self.data.get("scene_types", {}).get(self.combo_cat.currentText(), "")
        self.text_base.setText(f"{t} {c}")

    def get_current_settings(self):
        """
        Legacy method for getting settings (used by preset save and generate).
        Kept for backwards compatibility with PromptGenerator.
        """
        # Gather Global Light descriptions
        global_lights = {name: entry.text() for name, entry in self.light_defs.items()}
        
        # Get Seasons Data from Widget
        curr_seasons = self.seasons_widget.get_data(global_lights)

        return {
            "project_name": self.entry_name.text(),
            "context": self.entry_ctx.text(),
            "input_type": self.combo_type.currentText(),
            "scene_type": self.combo_cat.currentText(),
            "base_text": self.text_base.toPlainText().strip(),
            "xmas_desc": self.entry_xmas.text(),
            "global_rules": self.entry_rules.text(),
            "camera": self.entry_cam.text(),
            "active_seasons": curr_seasons, 
        }

    def save_state(self):
        """
        Override BaseTab's save_state to handle complex widgets.
        Simple fields are handled automatically via field registry.
        """
        # Call parent to save registered fields
        super().save_state()
        
        # Handle complex widgets manually
        config = config_helper.load_config()
        
        # Save global light definitions
        global_defs = {name: entry.text() for name, entry in self.light_defs.items()}
        config["constructor_global_lights_defs"] = global_defs
        
        # Save seasons data
        global_lights = {name: entry.text() for name, entry in self.light_defs.items()}
        curr_seasons = self.seasons_widget.get_data(global_lights)
        config["constructor_seasons"] = curr_seasons
        
        config_helper.save_config(config)

    def load_state(self):
        """
        Override BaseTab's load_state to handle complex widgets.
        Simple fields are handled automatically via field registry.
        """
        # Call parent to load registered fields
        super().load_state()
        
        config = config_helper.load_config()
        
        # Load global lighting definitions
        saved_defs = config.get("constructor_global_lights_defs", {})
        for l_name, l_entry in self.light_defs.items():
            if l_name in saved_defs:
                l_entry.setText(saved_defs[l_name])
        
        # Load seasons data
        saved_seasons = config.get("constructor_seasons", {})
        if saved_seasons:
            self.seasons_widget.set_data(saved_seasons)
        
        self.update_base_text()

    def on_save_preset_requested(self, name):
        data = self.get_current_settings()
        data["global_lights_defs"] = {n: e.text() for n, e in self.light_defs.items()}
        self.preset_bar.save_preset_data(name, data)

    def global_reset(self):
        self.entry_name.setText("New_Project")
        self.entry_ctx.setText("New Zeeland")
        self.entry_xmas.setText(self.data.get("christmas_desc", ""))
        self.entry_rules.setText(self.data.get("global_rules", ""))
        self.entry_cam.setText(self.data.get("camera", ""))
        
        # Reset Global Lighting Defs
        default_lights_data = self.data.get("lighting", {})
        for l_name, l_entry in self.light_defs.items():
            l_entry.setText(default_lights_data.get(l_name, ""))

        # Reset Tree Widget
        self.seasons_widget.reset_defaults()
            
        self.update_base_text()
        self.save_state()

    def apply_preset_data(self, data):
        self.entry_name.setText(data.get("project_name", "New_Project"))
        self.entry_ctx.setText(data.get("context", ""))
        self.combo_type.setCurrentText(data.get("input_type", "Viewport"))
        self.combo_cat.setCurrentText(data.get("scene_type", "Exterior"))
        
        self.entry_xmas.setText(data.get("xmas_desc", ""))
        self.entry_rules.setText(data.get("global_rules", ""))
        self.entry_cam.setText(data.get("camera", ""))
        
        # Global Lighting Descriptions
        saved_defs = data.get("global_lights_defs", {})
        for l_name, l_entry in self.light_defs.items():
            if l_name in saved_defs:
                l_entry.setText(saved_defs[l_name])

        # Delegate to Widget
        self.seasons_widget.set_data(data.get("active_seasons", {}))
        
        self.update_base_text()
        self.save_state()

    def generate(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not folder: return
        self.save_state()
        
        try:
            settings = self.get_current_settings()
            content = self.generator.generate_markdown(settings)
            
            if content.count("###") < 2:
                QMessageBox.warning(self, "No Prompts", "No active seasons or lights selected! Please check at least one season and one light in the hierarchy.")
                self.btn_gen.setText("GENERATE PROMPTS MATRIX")
                return

            out_file = Path(folder) / "prompts.md"
            out_file.write_text(content, encoding="utf-8")
            
            self.btn_gen.setText("SUCCESS!")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.btn_gen.setText("GENERATE PROMPTS MATRIX"))
            
        except Exception as e:
            self.btn_gen.setText(f"ERROR: {e}")
