import json
import os
from pathlib import Path
from core.utils.resource_helper import get_resource_path

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

    def reload_data(self):
        """Reloads template data from disk."""
        self.data = self._load_templates()
        return self.data

    def get_template_data(self) -> dict:
        return self.data

    def generate_markdown(self, settings):
        """
        Generates the markdown content based on the provided settings dictionary.
        """
        # Ensure we have fresh data
        self.reload_data()
        
        project_name = settings.get("project_name", "New Project")
        base = settings.get("base_text", "")
        ctx = settings.get("context", "")
        rules = settings.get("global_rules", "")
        camera = settings.get("camera", "")
        xmas_text = settings.get("xmas_desc", "")

        content = f"### {project_name}\n\n"

        active_seasons = settings.get("active_seasons", {})
        
        # Helper to write a block
        def write_block(title, s_name, s_atmos, light_txt, l_atmos="", is_xmas_variant=False):
            res = f"### {title}\n{base}\n"
            if ctx: res += f"- {ctx}\n"
            
            # Fallback for season text and atmosphere if empty in settings
            season_txt = s_data.get("season_text") or self.data.get("seasons", {}).get(s_name, s_name)
            atmos = s_atmos or self.data.get("default_atmospheres", {}).get(s_name, "")
            
            res += f"- {season_txt}\n- {atmos}\n"
            
            if l_atmos:
                res += f"- {l_atmos}\n"
            
            if light_txt:
                res += f"- {light_txt}\n"
            
            if rules: res += f"- {rules}\n"
            res += f"- {camera}\n\n"
            return res

        for s_name, s_data in active_seasons.items():
            if not s_data.get("is_active"): continue
            
            s_atmos = s_data.get("atmos", "")
            
            # Iterate lights nested in this season
            season_lights = s_data.get("lights", {})
            
            for l_name, l_data in season_lights.items():
                if not l_data.get("is_active"): continue
                
                # Fallback to global light description if empty
                l_desc = l_data.get("desc") or self.data.get("lighting", {}).get(l_name, "")
                l_atmos = l_data.get("atmos", "")
                is_xmas = l_data.get("is_xmas", False)
                
                # Standard Variant
                content += write_block(f"{s_name} + {l_name}", s_name, s_atmos, l_desc, l_atmos)
                
                # Xmas Variant (if checked for this specific light/season combo)
                if is_xmas:
                    x_atmos = s_atmos.rstrip('.') + f". {xmas_text}"
                    content += write_block(f"{s_name} + {l_name} + Xmas", s_name, x_atmos, l_desc, l_atmos, True)

        return content
