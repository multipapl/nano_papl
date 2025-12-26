import customtkinter as ctk
from tkinter import filedialog
import json
from pathlib import Path
from core.generator import PromptGenerator
from utils import config_helper

class TabConstructor(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=4)
        
        self.generator = PromptGenerator()
        self.data = self.generator.get_template_data()
        
        # Main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Top Bar (Reset Button)
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 0))
        
        self.btn_reset_all = ctk.CTkButton(top_bar, text="RESET ALL DEFAULTS", fg_color="#c0392b", hover_color="#a93226", height=32, corner_radius=4, command=self.global_reset)
        self.btn_reset_all.pack(side="right")
        
        # Scrollable Content
        self.scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=4)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self._setup_ui()
        self.load_state()

    def create_section_header(self, text, parent):
        ctk.CTkLabel(parent, text=text, font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=15, pady=(15, 5))

    def add_reset_btn(self, parent, target_entry, template_key, sub_key=None):
        def do_reset():
            val = ""
            if sub_key:
                val = self.data.get(template_key, {}).get(sub_key, "")
            else:
                val = self.data.get(template_key, "")
            
            if isinstance(target_entry, ctk.CTkTextbox):
                target_entry.delete("1.0", "end")
                target_entry.insert("1.0", val)
            else:
                target_entry.delete(0, 'end')
                target_entry.insert(0, val)

        btn = ctk.CTkButton(parent, text="↺", width=25, height=25, fg_color="transparent", text_color="#aaa", hover_color="#444", corner_radius=4, command=do_reset)
        btn.pack(side="right", padx=5)

    def _setup_ui(self):
        # --- Project Info Card ---
        self.create_section_header("PROJECT DETAILS", self.scroll_frame)
        card_proj = ctk.CTkFrame(self.scroll_frame, corner_radius=4)
        card_proj.pack(fill="x", padx=10, pady=5)
        
        # Title
        f_p = ctk.CTkFrame(card_proj, fg_color="transparent")
        f_p.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(f_p, text="Project Name:").pack(side="left", padx=(0, 10))
        self.project_name = ctk.CTkEntry(f_p, width=300, corner_radius=4)
        self.project_name.insert(0, "New_Project")
        self.project_name.pack(side="left", fill="x", expand=True)

        # Context
        f_c = ctk.CTkFrame(card_proj, fg_color="transparent")
        f_c.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(f_c, text="Context/Loc:").pack(side="left", padx=(0, 13))
        self.project_ctx = ctk.CTkEntry(f_c, corner_radius=4)
        self.project_ctx.pack(side="left", fill="x", expand=True)


        # --- Input & Scene Type ---
        self.create_section_header("SCENE CONFIGURATION", self.scroll_frame)
        card_scene = ctk.CTkFrame(self.scroll_frame, corner_radius=4)
        card_scene.pack(fill="x", padx=10, pady=5)
        
        f_sel = ctk.CTkFrame(card_scene, fg_color="transparent")
        f_sel.pack(fill="x", padx=10, pady=10)
        
        self.type_var = ctk.StringVar(value="Viewport")
        self.type_menu = ctk.CTkOptionMenu(f_sel, values=list(self.data.get("input_types", {}).keys()), variable=self.type_var, corner_radius=4, command=self.update_base_text)
        self.type_menu.pack(side="left", padx=(0, 10))

        self.cat_var = ctk.StringVar(value="Exterior")
        self.cat_menu = ctk.CTkOptionMenu(f_sel, values=list(self.data.get("scene_types", {}).keys()), variable=self.cat_var, corner_radius=4, command=self.update_base_text)
        self.cat_menu.pack(side="left")

        self.base_text = ctk.CTkTextbox(card_scene, height=60, font=("Consolas", 12), corner_radius=4)
        self.base_text.pack(fill="x", padx=10, pady=(0, 10))


        # --- Seasons ---
        self.create_section_header("SEASONS & ATMOSPHERE", self.scroll_frame)
        card_seasons = ctk.CTkFrame(self.scroll_frame, corner_radius=4)
        card_seasons.pack(fill="x", padx=10, pady=5)

        self.season_rows = {}
        for s_name, s_desc in self.data.get("seasons", {}).items():
            row = ctk.CTkFrame(card_seasons, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)
            
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(row, text=s_name, variable=var, width=80, corner_radius=4)
            cb.pack(side="left", padx=5)
            
            s_entry = ctk.CTkEntry(row, width=200, corner_radius=4)
            s_entry.insert(0, s_desc)
            s_entry.pack(side="left", padx=5)
            self.add_reset_btn(row, s_entry, "seasons", s_name)
            
            a_entry = ctk.CTkEntry(row, corner_radius=4)
            def_atmos = self.data.get("default_atmospheres", {}).get(s_name, "")
            a_entry.insert(0, def_atmos)
            a_entry.pack(side="left", padx=5, fill="x", expand=True)
            self.add_reset_btn(row, a_entry, "default_atmospheres", s_name)
            
            self.season_rows[s_name] = {"active": var, "season_txt": s_entry, "atmos_txt": a_entry}


        # --- Lighting ---
        self.create_section_header("LIGHTING SCENARIOS", self.scroll_frame)
        card_light = ctk.CTkFrame(self.scroll_frame, corner_radius=4)
        card_light.pack(fill="x", padx=10, pady=5)

        self.light_rows = {}
        for l_name, l_desc in self.data.get("lighting", {}).items():
            row = ctk.CTkFrame(card_light, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)
            
            l_var = ctk.BooleanVar(value=True)
            l_cb = ctk.CTkCheckBox(row, text=l_name, variable=l_var, width=120, corner_radius=4)
            l_cb.pack(side="left", padx=5)
            
            xmas_var = ctk.BooleanVar(value=False)
            xmas_cb = ctk.CTkCheckBox(row, text="Xmas", variable=xmas_var, width=60, text_color="#e74c3c", corner_radius=4)
            xmas_cb.pack(side="left", padx=5)
            
            l_entry = ctk.CTkEntry(row, corner_radius=4)
            l_entry.insert(0, l_desc)
            l_entry.pack(side="left", padx=5, fill="x", expand=True)
            self.add_reset_btn(row, l_entry, "lighting", l_name)
            
            self.light_rows[l_name] = {"active": l_var, "xmas": xmas_var, "light_txt": l_entry}


        # --- Footer Settings ---
        self.create_section_header("GLOBAL SETTINGS", self.scroll_frame)
        card_footer = ctk.CTkFrame(self.scroll_frame, corner_radius=4)
        card_footer.pack(fill="x", padx=10, pady=5)

        def add_setting_row(label, key, default_val=""):
            r = ctk.CTkFrame(card_footer, fg_color="transparent")
            r.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(r, text=label, width=120, anchor="w").pack(side="left")
            e = ctk.CTkEntry(r, corner_radius=4)
            e.pack(side="left", fill="x", expand=True)
            if key: self.add_reset_btn(r, e, key)
            return e

        self.xmas_desc_entry = add_setting_row("Xmas Description:", "christmas_desc")
        self.rules_entry = add_setting_row("Global Rules:", "global_rules")
        self.camera_entry = add_setting_row("Camera Settings:", "camera")


        # Generate Button Area
        self.btn_gen = ctk.CTkButton(self, text="GENERATE PROMPTS MATRIX", height=50, fg_color="#2ecc71", hover_color="#27ae60", font=("Arial", 15, "bold"), corner_radius=4, command=self.generate)
        self.btn_gen.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
        self.update_base_text()

    def update_base_text(self, *args):
        t = self.data.get("input_types", {}).get(self.type_var.get(), "")
        c = self.data.get("scene_types", {}).get(self.cat_var.get(), "")
        self.base_text.delete("1.0", "end")
        self.base_text.insert("1.0", f"{t} {c}")

    def get_current_settings(self):
        return {
            "project_name": self.project_name.get(),
            "context": self.project_ctx.get(),
            "input_type": self.type_var.get(),
            "scene_type": self.cat_var.get(),
            "base_text": self.base_text.get("1.0", "end-1c").strip(),
            "xmas_desc": self.xmas_desc_entry.get(),
            "global_rules": self.rules_entry.get(),
            "camera": self.camera_entry.get(),
            "active_seasons": {
                n: {
                    "is_active": r["active"].get(),
                    "season_text": r["season_txt"].get(),
                    "atmos": r["atmos_txt"].get()
                } for n, r in self.season_rows.items()
            },
            "active_lights": {
                n: {
                    "is_active": r["active"].get(),
                    "desc": r["light_txt"].get(),
                    "is_xmas": r["xmas"].get()
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
        self.project_name.delete(0, 'end'); self.project_name.insert(0, config.get("constructor_project_name", "New_Project"))
        self.project_ctx.delete(0, 'end'); self.project_ctx.insert(0, config.get("constructor_context", "New Zeeland"))
        self.type_var.set(config.get("constructor_input_type", "Viewport"))
        self.cat_var.set(config.get("constructor_scene_type", "Exterior"))
        
        self.xmas_desc_entry.delete(0, 'end'); self.xmas_desc_entry.insert(0, config.get("constructor_xmas_desc", ""))
        self.rules_entry.delete(0, 'end'); self.rules_entry.insert(0, config.get("constructor_global_rules", ""))
        self.camera_entry.delete(0, 'end'); self.camera_entry.insert(0, config.get("constructor_camera", ""))
        
        saved_seasons = config.get("constructor_seasons", {})
        for n, r in self.season_rows.items():
            if n in saved_seasons:
                s_data = saved_seasons[n]
                r["active"].set(s_data.get("is_active", False))
                r["season_txt"].delete(0, 'end'); r["season_txt"].insert(0, s_data.get("season_text", ""))
                r["atmos_txt"].delete(0, 'end'); r["atmos_txt"].insert(0, s_data.get("atmos", ""))
        
        saved_lights = config.get("constructor_lights", {})
        for n, r in self.light_rows.items():
            if n in saved_lights:
                l_data = saved_lights[n]
                r["active"].set(l_data.get("is_active", True))
                r["light_txt"].delete(0, 'end'); r["light_txt"].insert(0, l_data.get("desc", ""))
                r["xmas"].set(l_data.get("is_xmas", False))
        
        self.update_base_text()

    def global_reset(self):
        self.project_name.delete(0, 'end'); self.project_name.insert(0, "New_Project")
        self.project_ctx.delete(0, 'end'); self.project_ctx.insert(0, "New Zeeland")
        
        self.xmas_desc_entry.delete(0, 'end'); self.xmas_desc_entry.insert(0, self.data.get("christmas_desc", ""))
        self.rules_entry.delete(0, 'end'); self.rules_entry.insert(0, self.data.get("global_rules", ""))
        self.camera_entry.delete(0, 'end'); self.camera_entry.insert(0, self.data.get("camera", ""))

        for name, row in self.season_rows.items():
            row["active"].set(False)
            row["season_txt"].delete(0, 'end'); row["season_txt"].insert(0, self.data.get("seasons", {}).get(name, ""))
            row["atmos_txt"].delete(0, 'end'); row["atmos_txt"].insert(0, self.data.get("default_atmospheres", {}).get(name, ""))

        for name, row in self.light_rows.items():
            row["active"].set(True)
            row["xmas"].set(False)
            row["light_txt"].delete(0, 'end'); row["light_txt"].insert(0, self.data.get("lighting", {}).get(name, ""))
        
        self.update_base_text()
        self.save_state()

    def generate(self):
        folder = filedialog.askdirectory()
        if not folder: return
        self.save_state()
        
        try:
            settings = self.get_current_settings()
            content = self.generator.generate_markdown(settings)
            
            out_file = Path(folder) / "prompts.md"
            out_file.write_text(content, encoding="utf-8")
            
            self.btn_gen.configure(text="SUCCESS!", fg_color="#3498db", state="disabled")
            self.after(2000, lambda: self.btn_gen.configure(text="GENERATE PROMPTS MATRIX", fg_color="#2ecc71", state="normal"))
        except Exception as e:
            print(f"Error generating prompts: {e}")
            self.btn_gen.configure(text=f"ERROR: {e}", fg_color="#e74c3c")
