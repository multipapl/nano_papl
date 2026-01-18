from typing import Optional, Dict, Any
from pathlib import Path
import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QFileDialog, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from qfluentwidgets import (
    FluentIcon, InfoBar, InfoBarPosition, qconfig,
    BodyLabel, TextEdit, ComboBox, LineEdit, PrimaryPushButton,
    ToolButton, SegmentedWidget, PopUpAniStackedWidget as StackedWidget
)

from ui.components import ThemeAwareBackground, NPButton
from ui.widgets.constructor import (
    ModernPresetToolbar, SeasonMatrixOrchestrator, GeneralSetupWidget,
    SinglePromptWidget
)
from core.generator import PromptGenerator
from core.utils import config_helper
from core import constants
import logging

class ConstructorPage(ThemeAwareBackground):
    """
    Modern Constructor Page.
    Migrated from ui/tab_constructor.py
    
    Handles UI for prompt assembly, state management, and generation.
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        # Initialize inheritance chain
        super().__init__(parent)
        self.setObjectName("ConstructorPage")
        
        # State management (Local implementation to avoid touching legacy BaseTab)
        self.field_registry: Dict[str, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.generator = PromptGenerator()
        self.data = self.generator.get_template_data()
        
        self._setup_ui()
        self.load_state()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 10, 15, 10)
        self.main_layout.setSpacing(8)

        # 1. Preset Toolbar (Persistent at top)
        self.preset_bar = ModernPresetToolbar(
            presets_file=config_helper.PRESETS_FILE,
            show_reset=True,
            reset_label="Reset All Defaults",
            parent=self
        )
        self.preset_bar.preset_loaded.connect(self.apply_preset_data)
        self.preset_bar.save_requested.connect(self.on_save_preset_requested)
        self.preset_bar.reset_requested.connect(self.global_reset)
        self.main_layout.addWidget(self.preset_bar)

        # 2. Navigation bar (Segmented for better button look)
        nav_container = QWidget()
        nav_h_layout = QHBoxLayout(nav_container)
        nav_h_layout.setContentsMargins(0, 0, 0, 0)
        
        self.nav = SegmentedWidget(self)
        nav_h_layout.addStretch()
        nav_h_layout.addWidget(self.nav)
        nav_h_layout.addStretch()
        
        self.stacked_widget = StackedWidget(self)
        self.main_layout.addWidget(nav_container)
        self.main_layout.addWidget(self.stacked_widget, 1)

        self._setup_general_tab()
        self._setup_matrix_tab()
        self._setup_single_tab()

        # 3. Footer Action (Persistent at bottom)
        self.btn_gen = PrimaryPushButton("GENERATE PROMPTS MATRIX")
        self.btn_gen.setMinimumHeight(38)
        self.btn_gen.clicked.connect(self.generate)
        self.main_layout.addWidget(self.btn_gen)

    def _setup_general_tab(self):
        self.general_widget = GeneralSetupWidget(self.data, self)
        
        self.nav.addItem(
            routeKey="General",
            text="General Setup",
            onClick=lambda *args: (
                self.stacked_widget.setCurrentWidget(self.general_widget),
                self.btn_gen.show()
            ),
            icon=FluentIcon.EDIT
        )
        self.stacked_widget.addWidget(self.general_widget)

    def _setup_matrix_tab(self):
        self.matrix_widget = QWidget()
        layout = QVBoxLayout(self.matrix_widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        self.seasons_orchestrator = SeasonMatrixOrchestrator(self.data, self)
        layout.addWidget(self.seasons_orchestrator)

        self.nav.addItem(
            routeKey="Matrix",
            text="Seasons Matrix",
            onClick=lambda *args: (
                self.stacked_widget.setCurrentWidget(self.matrix_widget),
                self.btn_gen.show()
            ),
            icon=FluentIcon.SYNC
        )
        self.stacked_widget.addWidget(self.matrix_widget)

    def _setup_single_tab(self):
        self.single_widget = SinglePromptWidget(self.data, self)
        
        self.nav.addItem(
            routeKey="Single",
            text="Single Prompt",
            onClick=lambda *args: (
                self.stacked_widget.setCurrentWidget(self.single_widget),
                self.btn_gen.hide()
            ),
            icon=FluentIcon.DOCUMENT
        )
        self.stacked_widget.addWidget(self.single_widget)

    def get_current_settings(self):
        general_state = self.general_widget.get_state()
        global_lights = general_state.get("global_lights_defs", {})
        curr_seasons = self.seasons_orchestrator.get_state(global_lights)

        return {
            **general_state,
            "active_seasons": curr_seasons, 
            "single_prompt_state": self.single_widget.get_state()
        }

    def save_state(self):
        """Saves state from sub-widgets to config."""
        config = config_helper.load_config()
        
        general_state = self.general_widget.get_state()
        
        # Mapping to flat config keys
        mapping = {
            "project_name": "constructor_project_name",
            "context": "constructor_context",
            "input_type": "constructor_input_type",
            "scene_type": "constructor_scene_type",
            "base_text": "constructor_base_text",
            "xmas_desc": "constructor_xmas_desc",
            "global_rules": "constructor_global_rules",
            "camera": "constructor_camera",
            "global_lights_defs": "constructor_global_lights_defs"
        }
        
        for local_key, config_key in mapping.items():
            if local_key in general_state:
                config[config_key] = general_state[local_key]
        
        # Seasons
        global_defs = general_state.get("global_lights_defs", {})
        config["constructor_seasons"] = self.seasons_orchestrator.get_state(global_defs)
        
        # Single Prompt
        config["constructor_single_prompt"] = self.single_widget.get_state()
        
        config_helper.save_config(config)

    def load_state(self):
        """Loads state into sub-widgets from config."""
        config = config_helper.load_config()
        
        # Mapping from config to flat local dict
        mapping = {
            "constructor_project_name": "project_name",
            "constructor_context": "context",
            "constructor_input_type": "input_type",
            "constructor_scene_type": "scene_type",
            "constructor_base_text": "base_text",
            "constructor_xmas_desc": "xmas_desc",
            "constructor_global_rules": "global_rules",
            "constructor_camera": "camera",
            "constructor_global_lights_defs": "global_lights_defs"
        }
        
        general_data = {}
        for config_key, local_key in mapping.items():
            if config_key in config:
                general_data[local_key] = config[config_key]
        
        self.general_widget.set_state(general_data)
        
        # Seasons
        saved_seasons = config.get("constructor_seasons", {})
        if saved_seasons:
            self.seasons_orchestrator.set_state(saved_seasons)

        # Single Prompt
        saved_single = config.get("constructor_single_prompt", {})
        if saved_single:
            self.single_widget.set_state(saved_single)

    def on_save_preset_requested(self, name):
        data = self.get_current_settings()
        self.preset_bar.save_preset_data(name, data)
        InfoBar.success("Success", f"Preset '{name}' saved.", parent=self, position=InfoBarPosition.TOP)

    def global_reset(self):
        self.general_widget.reset_defaults()
        self.seasons_orchestrator.reset_defaults()
        self.single_widget.reset_defaults()
        self.save_state()
        InfoBar.info("Reset", "All fields reset to defaults.", parent=self, position=InfoBarPosition.TOP)

    def apply_preset_data(self, data):
        self.general_widget.set_state(data)
        self.seasons_orchestrator.set_state(data.get("active_seasons", {}))
        self.single_widget.set_state(data.get("single_prompt_state", {}))
        self.save_state()
        InfoBar.success("Preset Loaded", f"Applied settings from preset.", parent=self, position=InfoBarPosition.TOP)

    def generate(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not folder: return
        self.save_state()
        
        try:
            settings = self.get_current_settings()
            content = self.generator.generate_markdown(settings)
            
            if content.count("###") < 2:
                InfoBar.warning("No Prompts", "No active seasons or lights selected!", parent=self, position=InfoBarPosition.TOP)
                return

            out_file = Path(folder) / constants.DEFAULT_PROMPTS_FILE
            out_file.write_text(content, encoding="utf-8")
            
            InfoBar.success("Generation Complete", f"Prompts saved to {out_file}", parent=self, position=InfoBarPosition.TOP)
            
        except Exception as e:
            MessageBox("Error", f"Failed to generate prompts: {e}", self).exec()
