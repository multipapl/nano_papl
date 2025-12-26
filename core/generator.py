import json
from pathlib import Path

class PromptGenerator:
    def __init__(self, templates_file="templates.json"):
        self.templates_file = templates_file
        self.data = self._load_templates()

    def _load_templates(self):
        if Path(self.templates_file).exists():
            try:
                with open(self.templates_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                # Return empty if file is corrupt to prevent crash
                return {}
        return {}

    def get_template_data(self):
        return self.data

    def generate_markdown(self, settings):
        """
        Generates the markdown content based on the provided settings dictionary.
        settings structure expected:
        {
            "project_name": str,
            "base_text": str,
            "context": str,
            "global_rules": str,
            "camera": str,
            "xmas_desc": str,
            "active_seasons": { "SeasonName": {"atmos": "...", "is_active": bool} },
            "active_lights": { "LightName": {"desc": "...", "is_active": bool, "is_xmas": bool} }
        }
        """
        project_name = settings.get("project_name", "New Project")
        base = settings.get("base_text", "")
        ctx = settings.get("context", "")
        rules = settings.get("global_rules", "")
        camera = settings.get("camera", "")
        xmas_text = settings.get("xmas_desc", "")

        content = f"### {project_name}\n\n"

        active_seasons = settings.get("active_seasons", {})
        active_lights = settings.get("active_lights", {})

        for s_name, s_data in active_seasons.items():
            if not s_data.get("is_active"): continue
            
            for l_name, l_data in active_lights.items():
                if not l_data.get("is_active"): continue
                
                # Helper to write a block
                def write_block(title, atmos):
                    res = f"### {title}\n{base}\n"
                    if ctx: res += f"- {ctx}\n"
                    # We assume season text is standard or passed? 
                    # In legacy it was pulling from UI entry which pulled from template or user edit.
                    # We'll expect 'season_text' in s_data if possible, or just use name.
                    # Looking at legacy: "- {s_data['season_txt'].get()}\n- {atmos}\n"
                    season_txt = s_data.get("season_text", s_name)
                    
                    res += f"- {season_txt}\n- {atmos}\n"
                    
                    light_txt = l_data.get("desc", "")
                    res += f"- {light_txt}\n"
                    
                    if rules: res += f"- {rules}\n"
                    res += f"- {camera}\n\n"
                    return res

                # Normal generation
                atmos_val = s_data.get("atmos", "")
                content += write_block(f"{s_name} + {l_name}", atmos_val)

                # Xmas variant
                if s_name == "Winter" and l_data.get("is_xmas"):
                    atmos_x = atmos_val.rstrip('.') + f". {xmas_text}"
                    content += write_block(f"{s_name} + {l_name} + Xmas", atmos_x)

        return content
