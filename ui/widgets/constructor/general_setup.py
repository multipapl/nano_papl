from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFormLayout
from PySide6.QtCore import Qt
from qfluentwidgets import LineEdit, ComboBox, ToolButton, BodyLabel, FluentIcon
from ui.components import ThemeAwareBackground, SectionCard, AdaptiveTextEdit

class GeneralSetupWidget(QWidget):
    """
    Sub-interface for the 'General Setup' tab.
    Encapsulates Project Info, Scene Config, Lighting, and Global Settings.
    """
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.light_defs = {} # {name: LineEdit}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.viewport().setStyleSheet("background: transparent;")
        
        container = ThemeAwareBackground()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(15)

        # --- Project Info Card ---
        card_proj = SectionCard("Project Info")
        h_proj = QHBoxLayout()
        h_proj.setSpacing(20)
        
        form_p1 = QFormLayout()
        form_p1.setContentsMargins(0, 0, 0, 0)
        self.entry_name = LineEdit()
        self.entry_name.setPlaceholderText("New_Project")
        self.entry_name.setClearButtonEnabled(True)
        lbl_name = BodyLabel("Name:")
        lbl_name.setFixedWidth(50)
        form_p1.addRow(lbl_name, self.entry_name)
        h_proj.addLayout(form_p1, 1)

        form_p2 = QFormLayout()
        form_p2.setContentsMargins(0, 0, 0, 0)
        self.entry_ctx = LineEdit()
        self.entry_ctx.setPlaceholderText("Context/Location...")
        self.entry_ctx.setClearButtonEnabled(True)
        lbl_loc = BodyLabel("Loc:")
        lbl_loc.setFixedWidth(50)
        form_p2.addRow(lbl_loc, self.entry_ctx)
        h_proj.addLayout(form_p2, 1)
        
        card_proj.addLayout(h_proj)
        scroll_layout.addWidget(card_proj)

        # --- Scene Config Card ---
        card_scene = SectionCard("Scene Configuration")
        h_sel = QHBoxLayout()
        h_sel.setSpacing(20)
        
        form_s1 = QFormLayout()
        form_s1.setContentsMargins(0, 0, 0, 0)
        self.combo_type = ComboBox()
        self.combo_type.addItems(list(self.data.get("input_types", {}).keys()))
        self.combo_type.currentTextChanged.connect(self.update_base_text)
        lbl_input = BodyLabel("Input:")
        lbl_input.setFixedWidth(50)
        form_s1.addRow(lbl_input, self.combo_type)
        h_sel.addLayout(form_s1, 1)

        form_s2 = QFormLayout()
        form_s2.setContentsMargins(0, 0, 0, 0)
        self.combo_cat = ComboBox()
        self.combo_cat.addItems(list(self.data.get("scene_types", {}).keys()))
        self.combo_cat.currentTextChanged.connect(self.update_base_text)
        lbl_type = BodyLabel("Type:")
        lbl_type.setFixedWidth(50)
        form_s2.addRow(lbl_type, self.combo_cat)
        h_sel.addLayout(form_s2, 1)
        
        card_scene.addLayout(h_sel)

        self.text_base = AdaptiveTextEdit()
        self.text_base.setPlaceholderText("Adjust base prompt here...")
        card_scene.addWidget(self.text_base)
        scroll_layout.addWidget(card_scene)

        # --- Global Lighting Card ---
        card_lighting = SectionCard("Global Lighting Definitions")
        form_defs = QFormLayout()
        form_defs.setLabelAlignment(Qt.AlignRight)
        form_defs.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        default_lights = self.data.get("lighting", {})
        for l_name, l_desc in default_lights.items():
            h_row = QHBoxLayout()
            entry = LineEdit()
            entry.setText(l_desc)
            entry.setClearButtonEnabled(True)
            h_row.addWidget(entry)
            
            btn_reset = ToolButton(FluentIcon.SYNC)
            btn_reset.setFixedSize(30, 30)
            btn_reset.clicked.connect(lambda checked=False, e=entry, k="lighting", sk=l_name: self.reset_single_field(e, k, sk))
            h_row.addWidget(btn_reset)
            
            form_defs.addRow(BodyLabel(f"{l_name}:"), h_row)
            self.light_defs[l_name] = entry
            
        card_lighting.addLayout(form_defs)
        scroll_layout.addWidget(card_lighting)

        # --- Global Settings Card ---
        card_global = SectionCard("Global Settings & Rules")
        form_global = QFormLayout()
        form_global.setLabelAlignment(Qt.AlignRight)
        
        self.entry_xmas = LineEdit()
        self.entry_xmas.setPlaceholderText("Christmas variants suffix...")
        self.entry_xmas.setClearButtonEnabled(True)
        form_global.addRow(BodyLabel("Xmas Suffix:"), self.entry_xmas)
        
        self.entry_rules = LineEdit()
        self.entry_rules.setPlaceholderText("Global negative/positive rules...")
        self.entry_rules.setClearButtonEnabled(True)
        form_global.addRow(BodyLabel("Global Rules:"), self.entry_rules)
        
        self.entry_cam = LineEdit()
        self.entry_cam.setPlaceholderText("Camera, focal length, etc.")
        self.entry_cam.setClearButtonEnabled(True)
        form_global.addRow(BodyLabel("Camera:"), self.entry_cam)
        
        card_global.addLayout(form_global)
        scroll_layout.addWidget(card_global)

        scroll_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Initial call
        self.update_base_text()

    def update_base_text(self, *args):
        t = self.data.get("input_types", {}).get(self.combo_type.currentText(), "")
        c = self.data.get("scene_types", {}).get(self.combo_cat.currentText(), "")
        self.text_base.setText(f"{t} {c}")

    def reset_single_field(self, target, key, subkey=None):
        if subkey:
            val = self.data.get(key, {}).get(subkey, "")
        else:
            val = self.data.get(key, "")
        target.setText(val)

    def get_state(self) -> dict:
        return {
            "project_name": self.entry_name.text(),
            "context": self.entry_ctx.text(),
            "input_type": self.combo_type.currentText(),
            "scene_type": self.combo_cat.currentText(),
            "base_text": self.text_base.toPlainText().strip(),
            "xmas_desc": self.entry_xmas.text(),
            "global_rules": self.entry_rules.text(),
            "camera": self.entry_cam.text(),
            "global_lights_defs": {name: entry.text() for name, entry in self.light_defs.items()}
        }

    def set_state(self, data: dict):
        if not data: return
        self.entry_name.setText(data.get("project_name", "New_Project"))
        self.entry_ctx.setText(data.get("context", ""))
        self.combo_type.setCurrentText(data.get("input_type", "Viewport"))
        self.combo_cat.setCurrentText(data.get("scene_type", "Exterior"))
        self.text_base.setText(data.get("base_text", ""))
        self.entry_xmas.setText(data.get("xmas_desc", ""))
        self.entry_rules.setText(data.get("global_rules", ""))
        self.entry_cam.setText(data.get("camera", ""))
        
        saved_defs = data.get("global_lights_defs", {})
        for l_name, l_entry in self.light_defs.items():
            if l_name in saved_defs:
                l_entry.setText(saved_defs[l_name])
        
        self.update_base_text()

    def reset_defaults(self):
        self.entry_name.setText("New_Project")
        self.entry_ctx.setText("Default Location")
        self.entry_xmas.setText(self.data.get("christmas_desc", ""))
        self.entry_rules.setText(self.data.get("global_rules", ""))
        self.entry_cam.setText(self.data.get("camera", ""))
        
        default_lights_data = self.data.get("lighting", {})
        for l_name, l_entry in self.light_defs.items():
            l_entry.setText(default_lights_data.get(l_name, ""))
        self.update_base_text()
