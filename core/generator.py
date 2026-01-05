import json
import os
from pathlib import Path
from utils.resource_helper import get_resource_path

class PromptGenerator:
    def __init__(self, templates_file=os.path.join("data", "templates.json")):
        self.templates_file = get_resource_path(templates_file)
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

        active_seasons = settings.get("active_seasons", {}) # Now {Name: {is_active, ..., lights: {}}}
        # Legacy fallback if needed or just new structure
        
        # New Structure Iteration
        # active_seasons is dict: "Summer": { ... "lights": {...} }
        
        # We need to handle the case where "active_seasons" might be the old structure for a second
        # But since we update the UI first, ensuring new structure is key.
        # Actually, let's write robust code that expects the new structure as per plan.
        
        # Helper to write a block
        def write_block(title, atmos, light_txt, is_xmas_variant=False):
            res = f"### {title}\n{base}\n"
            if ctx: res += f"- {ctx}\n"
            
            season_txt = s_data.get("season_text", s_name)
            res += f"- {season_txt}\n- {atmos}\n"
            
            if light_txt:
                res += f"- {light_txt}\n"
            
            if rules: res += f"- {rules}\n"
            
            # Xmas check for rules/additions if needed, currently just desc in title/atmos
            
            res += f"- {camera}\n\n"
            return res

        for s_name, s_data in active_seasons.items():
            if not s_data.get("is_active"): continue
            
            # Season-specific atmosphere
            s_atmos = s_data.get("atmos", "")
            
            # Iterate lights nested in this season
            season_lights = s_data.get("lights", {})
            
            for l_name, l_data in season_lights.items():
                if not l_data.get("is_active"): continue
                
                l_desc = l_data.get("desc", "")
                is_xmas = l_data.get("is_xmas", False)
                
                # Standard Variant
                content += write_block(f"{s_name} + {l_name}", s_atmos, l_desc)
                
                # Xmas Variant (if checked for this specific light/season combo)
                if is_xmas:
                    # Append Xmas desc to atmosphere or separate line? 
                    # Previous logic: atmos.rstrip + xmas_text
                    x_atmos = s_atmos.rstrip('.') + f". {xmas_text}"
                    content += write_block(f"{s_name} + {l_name} + Xmas", x_atmos, l_desc, True)

        return content
