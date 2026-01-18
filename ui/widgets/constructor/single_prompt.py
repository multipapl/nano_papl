from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFormLayout
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    LineEdit, ComboBox, ToolButton, BodyLabel, FluentIcon, 
    CheckBox, CardWidget, SimpleCardWidget
)
from ui.components import ThemeAwareBackground, SectionCard, AdaptiveTextEdit, UIConfig

class SinglePromptWidget(QWidget):
    """
    Compact interface for real-time single prompt generation.
    """
    modified = Signal()

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self._setup_ui()
        self._connect_signals()
        self._apply_initial_defaults()
        self.update_prompt()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.viewport().setStyleSheet("background: transparent;")
        
        container = ThemeAwareBackground()
        self.scroll_layout = QVBoxLayout(container)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_layout.setSpacing(10)

        # 1. Compact Rows Card
        card_rows = SectionCard("Prompt Parameters")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(8)

        # Helper to create Row: ComboBox + LineEdit
        def create_combo_row(label_text, template_key):
            h = QHBoxLayout()
            combo = ComboBox()
            items = list(self.data.get(template_key, {}).keys())
            combo.addItems(items)
            
            entry = LineEdit()
            entry.setPlaceholderText("Edit template text...")
            entry.setClearButtonEnabled(True)
            
            h.addWidget(combo, 1)
            h.addWidget(entry, 2)
            
            lbl = BodyLabel(label_text)
            lbl.setFixedWidth(UIConfig.LABEL_MIN_WIDTH)
            form.addRow(lbl, h)
            return combo, entry

        # 1. Location
        self.entry_loc = LineEdit()
        self.entry_loc.setPlaceholderText("Location/Context...")
        self.entry_loc.setText("Default Location")
        lbl_loc = BodyLabel("Location:")
        lbl_loc.setFixedWidth(UIConfig.LABEL_MIN_WIDTH)
        form.addRow(lbl_loc, self.entry_loc)

        # 2. Input Type
        self.combo_input, self.entry_input = create_combo_row("Input:", "input_types")
        
        # 3. Scene Type
        self.combo_scene, self.entry_scene = create_combo_row("Type:", "scene_types")

        # 4. Season + Atmosphere
        h_season = QHBoxLayout()
        self.combo_season = ComboBox()
        self.combo_season.addItems(list(self.data.get("seasons", {}).keys()))
        self.entry_season = LineEdit()
        self.entry_season.setPlaceholderText("Season text...")
        self.entry_atmos = LineEdit()
        self.entry_atmos.setPlaceholderText("Atmosphere...")
        
        h_season.addWidget(self.combo_season, 1)
        h_season.addWidget(self.entry_season, 2)
        h_season.addWidget(self.entry_atmos, 2)
        
        lbl_season = BodyLabel("Season:")
        lbl_season.setFixedWidth(UIConfig.LABEL_MIN_WIDTH)
        form.addRow(lbl_season, h_season)

        # 5. Lighting
        self.combo_light, self.entry_light = create_combo_row("Lighting:", "lighting")

        # 6. Christmas
        h_xmas = QHBoxLayout()
        self.chk_xmas = CheckBox("Christmas Mode")
        self.entry_xmas = LineEdit()
        self.entry_xmas.setPlaceholderText("Christmas atmosphere description...")
        self.entry_xmas.setText(self.data.get("christmas_desc", ""))
        h_xmas.addWidget(self.chk_xmas)
        h_xmas.addWidget(self.entry_xmas, 1)
        
        form.addRow(BodyLabel("Xmas:"), h_xmas)

        # 7. Global Rules
        self.entry_rules = LineEdit()
        self.entry_rules.setPlaceholderText("Global rules...")
        self.entry_rules.setText(self.data.get("global_rules", ""))
        form.addRow(BodyLabel("Global:"), self.entry_rules)

        # 8. Camera
        self.entry_cam = LineEdit()
        self.entry_cam.setPlaceholderText("Camera settings...")
        self.entry_cam.setText(self.data.get("camera", ""))
        form.addRow(BodyLabel("Camera:"), self.entry_cam)

        card_rows.addLayout(form)
        self.scroll_layout.addWidget(card_rows)

        # --- Real-time Output ---
        self.text_out = AdaptiveTextEdit()
        self.text_out.setPlaceholderText("Generated prompt will appear here...")
        self.text_out.setReadOnly(True)
        # Make it look distinct
        self.text_out.setStyleSheet("QTextEdit { font-weight: bold; background: rgba(0,0,0,0.05); }")
        
        card_out = SectionCard("Live Preview")
        card_out.addWidget(self.text_out)
        self.scroll_layout.addWidget(card_out)

        self.scroll_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _connect_signals(self):
        # Connect combos to update their corresponding LineEdits
        self.combo_input.currentTextChanged.connect(
            lambda t: self.entry_input.setText(self.data.get("input_types", {}).get(t, ""))
        )
        self.combo_scene.currentTextChanged.connect(
            lambda t: self.entry_scene.setText(self.data.get("scene_types", {}).get(t, ""))
        )
        self.combo_season.currentTextChanged.connect(self._on_season_changed)
        self.combo_light.currentTextChanged.connect(
            lambda t: self.entry_light.setText(self.data.get("lighting", {}).get(t, ""))
        )

        # Connect all widgets to update_prompt
        widgets = [
            self.entry_loc, self.combo_input, self.entry_input,
            self.combo_scene, self.entry_scene, self.combo_season,
            self.entry_season, self.entry_atmos, self.combo_light,
            self.entry_light, self.chk_xmas, self.entry_xmas, 
            self.entry_rules, self.entry_cam
        ]
        for w in widgets:
            if isinstance(w, LineEdit):
                w.textChanged.connect(self.update_prompt)
            elif isinstance(w, ComboBox):
                w.currentTextChanged.connect(self.update_prompt)
            elif isinstance(w, CheckBox):
                w.stateChanged.connect(self.update_prompt)

    def _apply_initial_defaults(self):
        """Initial population of fields."""
        self.entry_input.setText(self.data.get("input_types", {}).get(self.combo_input.currentText(), ""))
        self.entry_scene.setText(self.data.get("scene_types", {}).get(self.combo_scene.currentText(), ""))
        self._on_season_changed(self.combo_season.currentText())
        self.entry_light.setText(self.data.get("lighting", {}).get(self.combo_light.currentText(), ""))

    def _on_season_changed(self, season_name):
        self.entry_season.setText(self.data.get("seasons", {}).get(season_name, ""))
        self.entry_atmos.setText(self.data.get("default_atmospheres", {}).get(season_name, ""))

    def update_prompt(self):
        input_type = self.entry_input.text().strip()
        scene_type = self.entry_scene.text().strip()
        loc = self.entry_loc.text().strip()
        season_text = self.entry_season.text().strip()
        atmos = self.entry_atmos.text().strip()
        light_txt = self.entry_light.text().strip()
        
        xmas = self.chk_xmas.isChecked()
        xmas_suffix = self.entry_xmas.text().strip() if xmas else ""
        
        rules = self.entry_rules.text().strip()
        cam = self.entry_cam.text().strip()

        # Assemble
        parts = [f"{input_type} {scene_type}"]
        if loc: parts.append(f"- {loc}")
        if season_text: parts.append(f"- {season_text}")
        
        if xmas and xmas_suffix:
            # Append xmas to atmosphere
            full_atmos = atmos.rstrip('.') + f". {xmas_suffix}"
            parts.append(f"- {full_atmos}")
        else:
            if atmos: parts.append(f"- {atmos}")
            
        if light_txt: parts.append(f"- {light_txt}")
        if rules: parts.append(f"- {rules}")
        if cam: parts.append(f"- {cam}")

        self.text_out.setText("\n".join(parts))
        self.modified.emit()

    def get_state(self) -> dict:
        return {
            "location": self.entry_loc.text(),
            "input_type_idx": self.combo_input.currentIndex(),
            "input_type_text": self.entry_input.text(),
            "scene_type_idx": self.combo_scene.currentIndex(),
            "scene_type_text": self.entry_scene.text(),
            "season_idx": self.combo_season.currentIndex(),
            "season_text": self.entry_season.text(),
            "atmosphere": self.entry_atmos.text(),
            "light_idx": self.combo_light.currentIndex(),
            "light_text": self.entry_light.text(),
            "is_christmas": self.chk_xmas.isChecked(),
            "xmas_text": self.entry_xmas.text(),
            "global_rules": self.entry_rules.text(),
            "camera": self.entry_cam.text()
        }

    def set_state(self, data: dict):
        if not data: return
        self.entry_loc.setText(data.get("location", "Default Location"))
        self.combo_input.setCurrentIndex(data.get("input_type_idx", 0))
        self.entry_input.setText(data.get("input_type_text", ""))
        self.combo_scene.setCurrentIndex(data.get("scene_type_idx", 0))
        self.entry_scene.setText(data.get("scene_type_text", ""))
        self.combo_season.setCurrentIndex(data.get("season_idx", 0))
        self.entry_season.setText(data.get("season_text", ""))
        self.entry_atmos.setText(data.get("atmosphere", ""))
        self.combo_light.setCurrentIndex(data.get("light_idx", 0))
        self.entry_light.setText(data.get("light_text", ""))
        self.chk_xmas.setChecked(data.get("is_christmas", False))
        self.entry_xmas.setText(data.get("xmas_text") or self.data.get("christmas_desc", ""))
        self.entry_rules.setText(data.get("global_rules") or self.data.get("global_rules", ""))
        self.entry_cam.setText(data.get("camera") or self.data.get("camera", ""))
        self.update_prompt()

    def reset_defaults(self):
        self.entry_loc.setText("Default Location")
        self.combo_input.setCurrentIndex(0)
        self.combo_scene.setCurrentIndex(0)
        self.combo_season.setCurrentIndex(0)
        self.combo_light.setCurrentIndex(0)
        self._apply_initial_defaults()
        self.chk_xmas.setChecked(False)
        self.entry_xmas.setText(self.data.get("christmas_desc", ""))
        self.entry_rules.setText(self.data.get("global_rules", ""))
        self.entry_cam.setText(self.data.get("camera", ""))
        self.update_prompt()
