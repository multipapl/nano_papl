import customtkinter as ctk
from tkinter import filedialog, Menu
import threading
import os
import datetime
import math
import re
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types
from utils import config_helper

class TabBatch(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=4)
        
        # Restore missing attributes
        self.stop_requested = False
        self.PROMPT_FILENAME = "prompts.md"
        # Try to load model_id from config, else use legacy default
        self.MODEL_ID = config_helper.get_value("model_id", "gemini-3-pro-image-preview")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Log area expands

        # UI Elements
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        # --- 1. Configuration Section ---
        config_frame = ctk.CTkFrame(self, corner_radius=4)
        config_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(config_frame, text="CONFIGURATION", font=("Arial", 12, "bold"), text_color="gray").grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        # API Key
        ctk.CTkLabel(config_frame, text="API Key:").grid(row=1, column=0, padx=15, pady=10, sticky="e")
        self.entry_key = ctk.CTkEntry(config_frame, placeholder_text="Paste your Google Gemini API Key here", corner_radius=4)
        self.entry_key.grid(row=1, column=1, padx=(0, 15), pady=10, sticky="ew")
        self.add_smart_menu(self.entry_key)

        # --- 2. Input/Output Paths ---
        paths_frame = ctk.CTkFrame(self, corner_radius=4)
        paths_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        paths_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(paths_frame, text="PATHS & SETTINGS", font=("Arial", 12, "bold"), text_color="gray").grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        # Input Path
        ctk.CTkLabel(paths_frame, text="Input Root:").grid(row=1, column=0, padx=15, pady=10, sticky="e")
        self.entry_in = ctk.CTkEntry(paths_frame, placeholder_text="Folder containing project subfolders", corner_radius=4)
        self.entry_in.grid(row=1, column=1, padx=(0, 5), pady=10, sticky="ew")
        self.btn_in = ctk.CTkButton(paths_frame, text="Browse", width=80, corner_radius=4, command=lambda: self.select_path(self.entry_in))
        self.btn_in.grid(row=1, column=2, padx=(0, 15), pady=10)
        self.add_smart_menu(self.entry_in)

        # Output Path
        ctk.CTkLabel(paths_frame, text="Output Folder:").grid(row=2, column=0, padx=15, pady=10, sticky="e")
        self.entry_out = ctk.CTkEntry(paths_frame, placeholder_text="Where to save generated images", corner_radius=4)
        self.entry_out.grid(row=2, column=1, padx=(0, 5), pady=10, sticky="ew")
        self.btn_out = ctk.CTkButton(paths_frame, text="Browse", width=80, corner_radius=4, command=lambda: self.select_path(self.entry_out))
        self.btn_out.grid(row=2, column=2, padx=(0, 15), pady=10)
        self.add_smart_menu(self.entry_out)

        # Settings Row (Resolution & Logs)
        settings_subframe = ctk.CTkFrame(paths_frame, fg_color="transparent")
        settings_subframe.grid(row=3, column=1, columnspan=2, sticky="w", pady=(0, 15))
        
        ctk.CTkLabel(settings_subframe, text="Resolution:").pack(side="left", padx=(0, 10))
        self.option_res = ctk.CTkOptionMenu(settings_subframe, values=["1K", "2K", "4K"], width=100, corner_radius=4)
        self.option_res.pack(side="left", padx=(0, 20))
        
        self.check_logs = ctk.CTkCheckBox(settings_subframe, text="Save Metadata Logs (.txt)", corner_radius=4)
        self.check_logs.select()
        self.check_logs.pack(side="left")

        # --- 3. Progress & Status ---
        status_frame = ctk.CTkFrame(self, corner_radius=4)
        status_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_rowconfigure(1, weight=1)

        # Progress Bar
        self.progress = ctk.CTkProgressBar(status_frame, corner_radius=4)
        self.progress.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        self.progress.set(0)

        # Console
        self.status_box = ctk.CTkTextbox(status_frame, font=("Consolas", 12), activate_scrollbars=True, corner_radius=4)
        self.status_box.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")

        # --- 4. Controls ---
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.btn_start = ctk.CTkButton(
            button_frame, text="START PROCESSING", fg_color="#2ecc71", hover_color="#27ae60", 
            text_color="white", height=50, font=("Arial", 14, "bold"), corner_radius=4,
            command=self.start_thread
        )
        self.btn_start.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.btn_stop = ctk.CTkButton(
            button_frame, text="STOP", fg_color="#e74c3c", hover_color="#c0392b", 
            text_color="white", height=50, font=("Arial", 14, "bold"), corner_radius=4,
            command=self.request_stop, state="disabled"
        )
        self.btn_stop.grid(row=0, column=1, padx=(10, 0), sticky="ew")

    def add_smart_menu(self, widget):
        menu = Menu(self, tearoff=0)
        
        def do_paste():
            try:
                text = self.clipboard_get()
                if widget.select_present():
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", text)
            except: pass

        def do_copy():
            try:
                if widget.select_present():
                    text = widget.get()[widget.index("sel.first"):widget.index("sel.last")]
                    self.clipboard_clear()
                    self.clipboard_append(text)
            except: pass

        menu.add_command(label="Cut", command=lambda: [do_copy(), widget.delete("sel.first", "sel.last")])
        menu.add_command(label="Copy", command=do_copy)
        menu.add_command(label="Paste", command=do_paste)
        
        def show_menu(event):
            widget.focus_set()
            menu.tk_popup(event.x_root, event.y_root)
        
        widget.bind("<Button-3>", show_menu)
        widget.bind("<Control-v>", lambda e: [do_paste(), "break"])
        widget.bind("<Control-c>", lambda e: [do_copy(), "break"])

    def select_path(self, entry_field):
        path = filedialog.askdirectory()
        if path:
            entry_field.delete(0, 'end')
            entry_field.insert(0, path)
            self.save_settings()

    def log(self, text):
        def _log():
            self.status_box.insert("end", f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {text}\n")
            self.status_box.see("end")
        self.after(0, _log)

    def save_settings(self):
        config_helper.set_value("api_key", self.entry_key.get().strip())
        config_helper.set_value("input_path", self.entry_in.get().strip())
        config_helper.set_value("output_path", self.entry_out.get().strip())
        config_helper.set_value("resolution", self.option_res.get())
        config_helper.set_value("generate_logs", self.check_logs.get())

    def load_settings(self):
        config = config_helper.load_config()
        self.entry_key.insert(0, config.get("api_key", ""))
        self.entry_in.insert(0, config.get("input_path", ""))
        self.entry_out.insert(0, config.get("output_path", ""))
        self.option_res.set(config.get("resolution", "1K"))
        if config.get("generate_logs", 1):
            self.check_logs.select()
        else:
            self.check_logs.deselect()

    def request_stop(self):
        self.stop_requested = True
        self.log("!!! STOP REQUESTED. Finishing current task... !!!")
        self.btn_stop.configure(state="disabled")

    def start_thread(self):
        self.save_settings()
        self.stop_requested = False
        threading.Thread(target=self.run_process, daemon=True).start()

    def reset_ui(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def get_smart_ratio(self, image_path):
        with Image.open(image_path) as img:
            w, h = img.size
            gcd = math.gcd(w, h)
            rw, rh = w // gcd, h // gcd
            if rw > 50 or rh > 50:
                target = w / h
                common = [(1,1), (16,9), (9,16), (4,3), (3,4), (21,9), (3,2), (2,3)]
                best = min(common, key=lambda r: abs(target - r[0]/r[1]))
                return f"{best[0]}:{best[1]}"
            return f"{rw}:{rh}"

    def parse_markdown_prompts(self, file_path):
        p = Path(file_path)
        if not p.exists(): return []
        content = p.read_text(encoding="utf-8")
        sections = re.split(r'\n###\s+', content)
        parsed = []
        for section in sections[1:]:
            lines = section.strip().split('\n')
            title = re.sub(r'[\\/*?:"<>|]', "", lines[0].strip().replace(" ", "_"))
            body = "\n".join(lines[1:]).strip()
            if body: parsed.append({"title": title, "prompt": body})
        return parsed

    def run_process(self):
        key = self.entry_key.get().strip()
        in_root = Path(self.entry_in.get().strip())
        out_root = Path(self.entry_out.get().strip())
        res_setting = self.option_res.get()

        if not key or not in_root.exists():
            self.log("CRITICAL ERROR: Invalid API Key or Input Path!")
            self.after(0, self.reset_ui)
            return

        def _init_ui():
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.status_box.delete("1.0", "end")
        self.after(0, _init_ui)
        
        self.log(f"--- INITIALIZING BATCH PROCESS ---")

        try:
            client = genai.Client(api_key=key)
            projects = [d for d in in_root.iterdir() if d.is_dir()]
            
            if not projects:
                self.log(f"WARNING: No project subfolders found.")
            
            valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
            
            for project_dir in projects:
                if self.stop_requested: break

                prompt_path = project_dir / self.PROMPT_FILENAME
                prompts_data = self.parse_markdown_prompts(prompt_path)
                
                if not prompts_data:
                    self.log(f"Skipping '{project_dir.name}': Prompts missing.")
                    continue
                
                images = [f for f in project_dir.iterdir() if f.suffix.lower() in valid_exts]
                project_out = out_root / project_dir.name
                project_out.mkdir(parents=True, exist_ok=True)

                for img_path in images:
                    if self.stop_requested: break
                    current_ratio = self.get_smart_ratio(img_path)
                    img_data = img_path.read_bytes()

                    for data in prompts_data:
                        if self.stop_requested: break
                        self.log(f"  [{project_dir.name}] {img_path.name} -> {data['title']}")
                        
                        try:
                            response = client.models.generate_content(
                                model=self.MODEL_ID,
                                contents=[
                                    data['prompt'],
                                    types.Part.from_bytes(data=img_data, mime_type="image/png")
                                ],
                                config=types.GenerateContentConfig(
                                    response_modalities=["IMAGE"],
                                )
                            )
                            
                            if response.parts:
                                for part in response.parts:
                                    if part.inline_data:
                                        ts = datetime.datetime.now().strftime("%H%M%S")
                                        base_name = f"{img_path.stem}_{data['title']}_{ts}"
                                        (project_out / f"{base_name}.png").write_bytes(part.inline_data.data)
                                        
                                        if self.check_logs.get():
                                            log_text = f"RATIO: {current_ratio}\nPROMPT:\n{data['prompt']}"
                                            (project_out / f"{base_name}.txt").write_text(log_text, encoding="utf-8")
                                        self.log(f"    [OK] Saved: {base_name}.png")

                        except Exception as e:
                            self.log(f"    [ERROR] API Call failed: {e}")

            if self.stop_requested:
                self.log("--- PROCESS STOPPED BY USER ---")
            else:
                self.log("--- BATCH PROCESS COMPLETED ---")
                self.after(0, lambda: self.progress.set(1))

        except Exception as e:
            self.log(f"CRITICAL SYSTEM ERROR: {e}")
        
        finally:
            self.after(0, self.reset_ui)
