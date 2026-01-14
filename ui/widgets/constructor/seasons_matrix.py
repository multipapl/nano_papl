from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    CheckBox, LineEdit, CaptionLabel, IconWidget, SwitchButton, 
    FluentIcon, BodyLabel, SegmentedWidget, PopUpAniStackedWidget as StackedWidget,
    SimpleCardWidget, CardWidget
)
from ui.components import ThemeAwareBackground

class SeasonGridWidget(ThemeAwareBackground):
    """
    Cleaner matrix view for a single season.
    Layout: Grid with columns [Active, Label, Description, Atmosphere, Xmas]
    """
    modified = Signal()

    def __init__(self, season_name: str, data_source: dict, parent=None):
        super().__init__(parent)
        self.season_name = season_name
        self.data_source = data_source
        self.light_rows = {} # {light_name: {widgets...}}
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Season Master Settings (Header)
        header_card = SimpleCardWidget(self)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(15)
        
        self.chk_active = CheckBox("Enable Season")
        self.chk_active.setChecked(True)
        self.chk_active.stateChanged.connect(lambda: self.modified.emit())
        header_layout.addWidget(self.chk_active)
        
        self.entry_desc = LineEdit()
        self.entry_desc.setPlaceholderText("Season general prompt suffix...")
        self.entry_desc.setText(self.data_source.get("seasons", {}).get(self.season_name, ""))
        self.entry_desc.setClearButtonEnabled(True)
        self.entry_desc.textChanged.connect(lambda: self.modified.emit())
        header_layout.addWidget(self.entry_desc, 2) # More weight
        
        self.entry_atmos = LineEdit()
        self.entry_atmos.setPlaceholderText("Global Atmosphere/Extras...")
        self.entry_atmos.setText(self.data_source.get("default_atmospheres", {}).get(self.season_name, ""))
        self.entry_atmos.setClearButtonEnabled(True)
        self.entry_atmos.textChanged.connect(lambda: self.modified.emit())
        header_layout.addWidget(self.entry_atmos, 1)
        
        layout.addWidget(header_card)

        # 2. Matrix Grid
        grid_card = CardWidget(self)
        grid_layout = QGridLayout(grid_card)
        grid_layout.setContentsMargins(15, 10, 15, 10)
        grid_layout.setSpacing(8) # Tighter vertical spacing
        grid_layout.setVerticalSpacing(4)

        # Columns Header Labels
        grid_layout.addWidget(CaptionLabel("Act"), 0, 0, Qt.AlignCenter)
        grid_layout.addWidget(CaptionLabel("Icon"), 0, 1, Qt.AlignCenter)
        grid_layout.addWidget(CaptionLabel("Type"), 0, 2)
        grid_layout.addWidget(CaptionLabel("Description Override (Placeholder = Global)"), 0, 3)
        grid_layout.addWidget(CaptionLabel("Atmosphere/Extras"), 0, 4)
        grid_layout.addWidget(CaptionLabel("Xmas"), 0, 5, Qt.AlignCenter)

        # Icon mapping
        icon_map = {
            "Daylight": FluentIcon.BRIGHTNESS,
            "Overcast": FluentIcon.SEND, 
            "Blue Hour": FluentIcon.HISTORY,
            "Night": FluentIcon.ROBOT
        }

        default_lights = self.data_source.get("lighting", {})
        row = 1
        for l_name in default_lights.keys():
            # Col 1: Active
            chk_l = CheckBox()
            chk_l.setChecked(True)
            chk_l.stateChanged.connect(lambda: self.modified.emit())
            grid_layout.addWidget(chk_l, row, 0, Qt.AlignCenter)

            # Col 2: Icon
            icon_w = IconWidget(icon_map.get(l_name, FluentIcon.INFO), self)
            icon_w.setFixedSize(16, 16)
            grid_layout.addWidget(icon_w, row, 1, Qt.AlignCenter)

            # Col 3: Label
            lbl_l = BodyLabel(l_name)
            grid_layout.addWidget(lbl_l, row, 2)

            # Col 4: Description (Weight ~50%)
            entry_l = LineEdit()
            entry_l.setPlaceholderText(f"Use global: {default_lights.get(l_name, '')}")
            entry_l.setClearButtonEnabled(True)
            entry_l.textChanged.connect(lambda: self.modified.emit())
            grid_layout.addWidget(entry_l, row, 3)
            grid_layout.setColumnStretch(3, 50)

            # Col 5: Extras
            entry_a = LineEdit()
            entry_a.setPlaceholderText("Atmosphere...")
            entry_a.setClearButtonEnabled(True)
            entry_a.textChanged.connect(lambda: self.modified.emit())
            grid_layout.addWidget(entry_a, row, 4)
            grid_layout.setColumnStretch(4, 30)

            # Col 6: Xmas Mode (SwitchButton)
            sw_x = SwitchButton()
            sw_x.checkedChanged.connect(lambda: self.modified.emit())
            grid_layout.addWidget(sw_x, row, 5, Qt.AlignCenter)

            self.light_rows[l_name] = {
                "chk": chk_l,
                "desc": entry_l,
                "atmos": entry_a,
                "xmas": sw_x
            }
            row += 1
            
        layout.addWidget(grid_card)
        layout.addStretch()

    def get_state(self, global_lights_map: dict) -> dict:
        curr_lights = {}
        for l_name, widgets in self.light_rows.items():
            # Save only if it's an actual override
            desc_override = widgets["desc"].text().strip()
            
            curr_lights[l_name] = {
                "is_active": widgets["chk"].isChecked(),
                "desc_override": desc_override,
                "is_xmas": widgets["xmas"].isChecked(),
                "atmos_override": widgets["atmos"].text().strip()
            }

        return {
            "is_active": self.chk_active.isChecked(),
            "season_text": self.entry_desc.text().strip(),
            "atmos": self.entry_atmos.text().strip(),
            "lights": curr_lights
        }

    def set_state(self, data: dict):
        self.chk_active.setChecked(data.get("is_active", True))
        self.entry_desc.setText(data.get("season_text", ""))
        self.entry_atmos.setText(data.get("atmos", ""))
        
        lights_data = data.get("lights", {})
        for l_name, widgets in self.light_rows.items():
            if l_name in lights_data:
                l_config = lights_data[l_name]
                widgets["chk"].setChecked(l_config.get("is_active", True))
                widgets["desc"].setText(l_config.get("desc_override", "")) 
                widgets["xmas"].setChecked(l_config.get("is_xmas", False))
                widgets["atmos"].setText(l_config.get("atmos_override", ""))

class SeasonMatrixOrchestrator(QWidget):
    """
    Manages multiple SeasonGridWidgets using a SegmentedWidget + StackedWidget.
    """
    modified = Signal()

    def __init__(self, data_source: dict, parent=None):
        super().__init__(parent)
        self.data_source = data_source
        self.season_widgets = {} # {season_name: SeasonGridWidget}
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 1. Segmented Control
        self.segmented_widget = SegmentedWidget(self)
        layout.addWidget(self.segmented_widget)

        # 2. Stacked Area
        self.stacked_widget = StackedWidget(self)
        layout.addWidget(self.stacked_widget)

        seasons_list = ["Winter", "Autumn", "Spring", "Summer"]
        for s_name in seasons_list:
            grid = SeasonGridWidget(s_name, self.data_source, self)
            grid.modified.connect(lambda: self.modified.emit())
            self.season_widgets[s_name] = grid
            
            # Add to stack and segmented
            self.stacked_widget.addWidget(grid)
            self.segmented_widget.addItem(
                routeKey=s_name,
                text=s_name,
                onClick=lambda checked, name=s_name: self.stacked_widget.setCurrentWidget(self.season_widgets[name])
            )

        # Default selection
        if seasons_list:
            self.segmented_widget.setCurrentItem(seasons_list[0])
            self.stacked_widget.setCurrentWidget(self.season_widgets[seasons_list[0]])

    def get_state(self, global_lights_map: dict) -> dict:
        state = {}
        for s_name, widget in self.season_widgets.items():
            state[s_name] = widget.get_state(global_lights_map)
        return state

    def set_state(self, data: dict):
        for s_name, widget in self.season_widgets.items():
            if s_name in data:
                widget.set_state(data[s_name])
                
    def reset_defaults(self):
        for widget in self.season_widgets.values():
            widget.chk_active.setChecked(True)
