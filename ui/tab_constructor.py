from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QScrollArea, QCheckBox, QComboBox, QGroupBox, QFileDialog, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QFrame, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt
import os
import json
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
        
        # Reset & Presets Button Bar
        top_bar = QHBoxLayout()
        
        top_bar.addWidget(QLabel("Presets:"))
        self.combo_presets = QComboBox()
        self.combo_presets.setMinimumWidth(200)
        top_bar.addWidget(self.combo_presets)
        
        btn_load_p = QPushButton("Load")
        btn_load_p.clicked.connect(self.on_load_preset)
        top_bar.addWidget(btn_load_p)
        
        btn_save_p = QPushButton("Save As...")
        btn_save_p.clicked.connect(self.on_save_preset)
        top_bar.addWidget(btn_save_p)
        
        btn_del_p = QPushButton("Delete")
        btn_del_p.setStyleSheet("color: #e74c3c;")
        btn_del_p.clicked.connect(self.on_delete_preset)
        top_bar.addWidget(btn_del_p)

        top_bar.addStretch()
        
        btn_reset = QPushButton("Reset All Defaults")
        btn_reset.setStyleSheet("background-color: #d32f2f; color: white; border-radius: 4px; padding: 5px 10px;")
        btn_reset.clicked.connect(self.global_reset)
        top_bar.addWidget(btn_reset)
        main_layout.addLayout(top_bar)
        
        self.PRESETS_FILE = config_helper.PRESETS_FILE
        self.refresh_presets_list()

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

        # --- Lighting Definitions (Global) ---
        grp_lighting_defs = QGroupBox("Global Lighting Definitions")
        l_defs = QVBoxLayout()
        self.light_defs = {} # Store line edits: {name: QLineEdit}
        
        default_lights = self.data.get("lighting", {})
        
        for l_name, l_desc in default_lights.items():
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{l_name}:"))
            entry = QLineEdit(l_desc)
            self.create_reset_btn(entry, "lighting", l_name, row)
            row.insertWidget(1, entry)
            l_defs.addLayout(row)
            self.light_defs[l_name] = entry
            
        grp_lighting_defs.setLayout(l_defs)
        self.content_layout.addWidget(grp_lighting_defs)

        # --- Seasons & Lighting Hierarchy ---
        grp_tree = QGroupBox("Seasons Lighting Hierarchy")
        l_tree = QVBoxLayout()
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Selection / Name", "Description / Details", "Atmosphere / Extras"])
        self.tree.setColumnWidth(0, 250)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)

        for s_name, s_desc in self.data.get("seasons", {}).items():
            # Top Level: Season
            item_season = QTreeWidgetItem(self.tree)
            
            # Col 0: Checkbox + Name
            chk_season = QCheckBox(s_name)
            chk_season.setChecked(True) # Default all ON (Fix: was unchecked)
            self.tree.setItemWidget(item_season, 0, chk_season)
            
            # Col 1: Description
            entry_s_desc = QLineEdit(s_desc)
            self.tree.setItemWidget(item_season, 1, entry_s_desc)
            
            # Col 2: Atmosphere
            default_atmos = self.data.get("default_atmospheres", {}).get(s_name, "")
            entry_atmos = QLineEdit(default_atmos)
            entry_atmos.setPlaceholderText("Atmosphere...")
            self.tree.setItemWidget(item_season, 2, entry_atmos)
            
            # Store references in item for easy access later
            item_season.setData(0, Qt.UserRole, {"type": "season", "name": s_name, "chk": chk_season, "desc": entry_s_desc, "atmos": entry_atmos})

            # Children: Lighting (Simplified)
            for l_name in default_lights.keys():
                item_light = QTreeWidgetItem(item_season)
                
                # Col 0: Checkbox + Name
                chk_light = QCheckBox(l_name)
                chk_light.setChecked(True) # Default all ON
                self.tree.setItemWidget(item_light, 0, chk_light)
                
                # Col 1: Empty (Description moved to Global)
                
                # Col 2: Xmas Checkbox
                chk_xmas = QCheckBox("Xmas Variant")
                chk_xmas.setStyleSheet("color: #e74c3c")
                self.tree.setItemWidget(item_light, 2, chk_xmas)
                
                item_light.setData(0, Qt.UserRole, {"type": "light", "name": l_name, "chk": chk_light, "xmas": chk_xmas})

        l_tree.addWidget(self.tree)
        grp_tree.setLayout(l_tree)
        self.content_layout.addWidget(grp_tree)

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
        # Traverse Tree
        curr_seasons = {}
        
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item_s = root.child(i)
            data_s = item_s.data(0, Qt.UserRole)
            s_name = data_s["name"]
            
            # Get Children (Lights)
            curr_lights = {}
            for j in range(item_s.childCount()):
                item_l = item_s.child(j)
                data_l = item_l.data(0, Qt.UserRole)
                l_name = data_l["name"]
                
                # Use Global Description
                global_desc = self.light_defs[l_name].text()
                
                curr_lights[l_name] = {
                    "is_active": data_l["chk"].isChecked(),
                    "desc": global_desc,
                    "is_xmas": data_l["xmas"].isChecked()
                }

            curr_seasons[s_name] = {
                "is_active": data_s["chk"].isChecked(),
                "season_text": data_s["desc"].text(),
                "atmos": data_s["atmos"].text(),
                "lights": curr_lights
            }

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
            # active_lights is no longer global, it's nested.
            # We keep structure compatible with generator update.
        }

    def save_state(self):
        settings = self.get_current_settings()
        
        # Extract Global Defs for separate saving
        global_defs = {name: entry.text() for name, entry in self.light_defs.items()}
        
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
            "constructor_global_lights_defs": global_defs 
            # Note: We save global defs separately so they persist even if a specific season/light combo wasn't active
        })
        config_helper.save_config(full_config)

    def load_state(self):
        config = config_helper.load_config()
        
        # Map config keys to preset-style keys for apply_preset_data
        mapped_data = {
            "project_name": config.get("constructor_project_name", "New_Project"),
            "context": config.get("constructor_context", "New Zeeland"),
            "input_type": config.get("constructor_input_type", "Viewport"),
            "scene_type": config.get("constructor_scene_type", "Exterior"),
            "xmas_desc": config.get("constructor_xmas_desc", ""),
            "global_rules": config.get("constructor_global_rules", ""),
            "camera": config.get("constructor_camera", ""),
            "global_lights_defs": config.get("constructor_global_lights_defs", {}),
            "active_seasons": config.get("constructor_seasons", {})
        }
        
        self.apply_preset_data(mapped_data)

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

        # Traverse Tree
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item_s = root.child(i)
            data_s = item_s.data(0, Qt.UserRole)
            s_name = data_s["name"]
            
            # Reset Season
            data_s["chk"].setChecked(False)
            data_s["desc"].setText(self.data.get("seasons", {}).get(s_name, ""))
            data_s["atmos"].setText(self.data.get("default_atmospheres", {}).get(s_name, ""))
            
            # Reset Lights
            for j in range(item_s.childCount()):
                item_l = item_s.child(j)
                data_l = item_l.data(0, Qt.UserRole)
                l_name = data_l["name"]
                
                data_l["chk"].setChecked(True)
                data_l["xmas"].setChecked(False)
            
        self.update_base_text()
        self.save_state()

    def refresh_presets_list(self):
        self.combo_presets.clear()
        presets = self._load_all_presets()
        self.combo_presets.addItems(sorted(presets.keys()))

    def _load_all_presets(self):
        if os.path.exists(self.PRESETS_FILE):
            try:
                with open(self.PRESETS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_all_presets(self, presets):
        with open(self.PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=4, ensure_ascii=False)

    def on_save_preset(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        if ok and name.strip():
            presets = self._load_all_presets()
            presets[name.strip()] = self.get_current_settings()
            # Also include global defs in the preset for full restoration
            presets[name.strip()]["global_lights_defs"] = {n: e.text() for n, e in self.light_defs.items()}
            
            self._save_all_presets(presets)
            self.refresh_presets_list()
            self.combo_presets.setCurrentText(name.strip())

    def on_load_preset(self):
        name = self.combo_presets.currentText()
        if not name: return
        
        presets = self._load_all_presets()
        if name in presets:
            self.apply_preset_data(presets[name])

    def on_delete_preset(self):
        name = self.combo_presets.currentText()
        if not name: return
        
        reply = QMessageBox.question(self, "Delete Preset", f"Are you sure you want to delete '{name}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            presets = self._load_all_presets()
            if name in presets:
                del presets[name]
                self._save_all_presets(presets)
                self.refresh_presets_list()

    def apply_preset_data(self, data):
        # We refactor load_state logic here to apply external dict
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

        saved_seasons = data.get("active_seasons", {})
        
        # Traverse Tree and Apply Checks
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item_s = root.child(i)
            data_s = item_s.data(0, Qt.UserRole)
            s_name = data_s["name"]
            
            if s_name in saved_seasons:
                s_conf = saved_seasons[s_name]
                data_s["chk"].setChecked(s_conf.get("is_active", False))
                data_s["desc"].setText(s_conf.get("season_text", ""))
                data_s["atmos"].setText(s_conf.get("atmos", ""))
                
                # Lights
                saved_lights = s_conf.get("lights", {})
                for j in range(item_s.childCount()):
                    item_l = item_s.child(j)
                    data_l = item_l.data(0, Qt.UserRole)
                    l_name = data_l["name"]
                    
                    if l_name in saved_lights:
                        l_conf = saved_lights[l_name]
                        data_l["chk"].setChecked(l_conf.get("is_active", True))
                        data_l["xmas"].setChecked(l_conf.get("is_xmas", False))
        
        self.update_base_text()
        self.save_state()

    def generate(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not folder: return
        self.save_state()
        
        try:
            settings = self.get_current_settings()
            content = self.generator.generate_markdown(settings)
            
            # Validation: Prevent empty prompt files
            # The generator returns a title even if no blocks were added, 
            # so we check if there are any actual prompt blocks (### Season + Light)
            if content.count("###") < 2:
                QMessageBox.warning(self, "No Prompts", "No active seasons or lights selected! Please check at least one season and one light in the hierarchy.")
                self.btn_gen.setText("GENERATE PROMPTS MATRIX")
                return

            out_file = Path(folder) / "prompts.md"
            out_file.write_text(content, encoding="utf-8")
            
            self.btn_gen.setText("SUCCESS!")
            # In Qt we use QTimer for delayed actions on UI
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.btn_gen.setText("GENERATE PROMPTS MATRIX"))
            
        except Exception as e:
            self.btn_gen.setText(f"ERROR: {e}")
