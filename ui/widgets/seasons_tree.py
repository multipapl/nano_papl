from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QCheckBox, QLineEdit, QHeaderView
)
from PySide6.QtCore import Qt
from ui.styles import Colors, Styles
from ui.widgets.stateful_widget import StatefulWidget

class SeasonsTreeWidget(StatefulWidget):
    """
    A specialized widget for managing Seasons and Lighting hierarchy.
    Handles population, interaction, and data extraction.
    Implements StatefulWidget protocol for automated state management.
    """
    def __init__(self, data_source):
        super().__init__()
        self.data_source = data_source # The full template data
        self.global_lights_map = {}  # Store for get_state
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Selection / Name", "Description / Details", "Atmosphere / Extras"])
        
        # Responsive Columns
        self.tree.setColumnWidth(0, 250)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Default height, but allow shrinking if in a scroll area constrained layout?
        # Better to let it grow.
        self.tree.setMinimumHeight(200) 
        
        layout.addWidget(self.tree)
        self.populate_tree()

    def populate_tree(self):
        self.tree.clear()
        seasons = self.data_source.get("seasons", {})
        default_lights = self.data_source.get("lighting", {}) # Keys used for structure
        default_atmos = self.data_source.get("default_atmospheres", {})

        for s_name, s_desc in seasons.items():
            # Top Level: Season
            item_season = QTreeWidgetItem(self.tree)
            
            # Col 0: Checkbox + Name
            chk_season = QCheckBox(s_name)
            chk_season.setChecked(True) 
            self.tree.setItemWidget(item_season, 0, chk_season)
            
            # Col 1: Description
            entry_s_desc = QLineEdit(s_desc)
            entry_s_desc.setStyleSheet(Styles.INPUT_FIELD)
            self.tree.setItemWidget(item_season, 1, entry_s_desc)
            
            # Col 2: Atmosphere
            entry_atmos = QLineEdit(default_atmos.get(s_name, ""))
            entry_atmos.setPlaceholderText("Atmosphere...")
            entry_atmos.setStyleSheet(Styles.INPUT_FIELD)
            self.tree.setItemWidget(item_season, 2, entry_atmos)
            
            # Store references
            item_season.setData(0, Qt.UserRole, {
                "type": "season", 
                "name": s_name, 
                "chk": chk_season, 
                "desc": entry_s_desc, 
                "atmos": entry_atmos
            })

            # Children: Lighting
            for l_name in default_lights.keys():
                item_light = QTreeWidgetItem(item_season)
                
                # Col 0: Checkbox + Name
                chk_light = QCheckBox(l_name)
                chk_light.setChecked(True)
                self.tree.setItemWidget(item_light, 0, chk_light)
                
                # Col 2: Xmas Checkbox
                chk_xmas = QCheckBox("Xmas Variant")
                chk_xmas.setStyleSheet(f"color: {Colors.DANGER}")
                self.tree.setItemWidget(item_light, 2, chk_xmas)
                
                item_light.setData(0, Qt.UserRole, {
                    "type": "light", 
                    "name": l_name, 
                    "chk": chk_light, 
                    "xmas": chk_xmas
                })

        self.tree.expandAll()

    def get_state(self, global_lights_map=None):
        """
        Extracts state (implementing StatefulWidget protocol).
        global_lights_map: dict of {light_name: current_description} from the Global definitions.
        """
        if global_lights_map is not None:
            self.global_lights_map = global_lights_map
        
        curr_seasons = {}
        root = self.tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            item_s = root.child(i)
            data_s = item_s.data(0, Qt.UserRole)
            s_name = data_s["name"]
            
            curr_lights = {}
            for j in range(item_s.childCount()):
                item_l = item_s.child(j)
                data_l = item_l.data(0, Qt.UserRole)
                l_name = data_l["name"]
                
                # Use Global Description passed in
                global_desc = self.global_lights_map.get(l_name, "")
                
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
        return curr_seasons
    
    def get_data(self, global_lights_map):
        """Backwards compatibility wrapper for get_state"""
        return self.get_state(global_lights_map)

    def set_state(self, saved_seasons):
        """
        Restores state from saved dictionary.
        """
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
                
                saved_lights = s_conf.get("lights", {})
                for j in range(item_s.childCount()):
                    item_l = item_s.child(j)
                    data_l = item_l.data(0, Qt.UserRole)
                    l_name = data_l["name"]
                    
                    if l_name in saved_lights:
                        l_conf = saved_lights[l_name]
                        data_l["chk"].setChecked(l_conf.get("is_active", True))
                        data_l["xmas"].setChecked(l_conf.get("is_xmas", False))
    
    def set_data(self, saved_seasons):
        """Backwards compatibility wrapper for set_state"""
        self.set_state(saved_seasons)

    def reset_defaults(self):
        """Resets all fields to template defaults."""
        self.populate_tree()
