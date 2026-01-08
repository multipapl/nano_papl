import datetime
from pathlib import Path
from PIL import Image
import io
import google.genai as genai
from google.genai import types
from core.utils.path_provider import PathProvider

class GenerationService:
    """
    Service responsible for generating images using AI providers (currently Google GenAI).
    Handles API communication, image processing, and file saving.
    """
    def __init__(self, api_key, model_id="gemini-3-pro-image-preview"):
        self.api_key = api_key
        self.model_id = model_id
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
        
        self.path_provider = PathProvider()

    def generate_image(self, prompt_data, image_path: Path, output_config: dict) -> dict:
        """
        Generates an image based on prompt and input image.
        
        Args:
            prompt_data (dict): Contains 'prompt' and 'title'.
            image_path (Path): Path to source image.
            output_config (dict): {
                'resolution': str,
                'ratio': str, # 'Manual' or specific '16:9'
                'format': str, # 'PNG' or 'JPG'
                'project_out_dir': Path 
            }
            
        Returns:
            dict: Result info {
                'success': bool,
                'saved_path': Path,
                'error': str,
                'is_diff_resolution': bool
            }
        """
        if not self.client:
            return {'success': False, 'error': "API Key missing"}

        try:
            # 1. Prepare Image
            with Image.open(image_path) as img:
                img_data = io.BytesIO()
                img.save(img_data, format=img.format)
                img_bytes = img_data.getvalue()
                
                # Input resolution for comparison
                in_w, in_h = img.size

            # 2. Mime Type
            mime_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.webp': 'image/webp'
            }
            mime_type = mime_map.get(image_path.suffix.lower(), 'image/png')

            # 3. Config
            resolution = output_config.get('resolution', '1K')
            ratio_mode = output_config.get('ratio', '1:1')
            
            image_config_params = {"image_size": resolution}
            
            # Helper to calculate ratio if Manual (moved from BatchWorker logic, could be utility)
            # For now, relying on the value passed being either "Manual" or a ratio string.
            # If "Manual", the caller (BatchWorker) might have already calculated it or we calculate here.
            # BatchWorker previously called `get_smart_ratio`. Let's assume we do it here if needed.
            
            if ratio_mode == "Manual":
                # We need util import, or duplicate logic. 
                # Better to use the util. existing code imported `image_utils` from `utils`.
                # I will add import at top.
                from core.utils import image_utils
                ratio_val = image_utils.get_smart_ratio(image_path)
                image_config_params["aspect_ratio"] = ratio_val
            elif ratio_mode != "Auto": # If not Auto and not Manual, it's specific
                 image_config_params["aspect_ratio"] = ratio_mode

            gen_config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(**image_config_params),
                temperature=0.4
            )

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt_data['prompt']),
                        types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
                    ]
                )
            ]

            # 4. API Call
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=contents,
                config=gen_config
            )

            # 5. Process Response
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        # 6. Save & Verify
                         return self._save_generated_image(
                            part.inline_data.data, 
                            prompt_data, 
                            image_path, 
                            output_config,
                            (in_w, in_h)
                        )
            
            return {'success': False, 'error': "No image in response"}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _save_generated_image(self, img_data, prompt_data, source_path, config, input_size):
        try:
            generated_img = Image.open(io.BytesIO(img_data))
            gen_w, gen_h = generated_img.size
            in_w, in_h = input_size

            # Check Differences
            is_diff = (gen_w != in_w) or (gen_h != in_h)
            suffix = "_diff" if is_diff else ""

            # Filename Construction
            ts = datetime.datetime.now().strftime("%H%M%S")
            clean_title = prompt_data['title'].replace("_+_", "+").replace(" + ", "+")
            clean_stem = source_path.stem.replace("_optimized", "")
            base_name = f"{clean_stem}_{clean_title}_{ts}{suffix}"

            # Output Path
            project_out = config.get('project_out_dir')
            # Subfolder for this specific image source
            image_out_dir = project_out / clean_stem
            image_out_dir.mkdir(parents=True, exist_ok=True)

            out_fmt = config.get('format', 'PNG')
            ext = ".png" if out_fmt == "PNG" else ".jpg"
            save_path = image_out_dir / f"{base_name}{ext}"

            # Saving
            if out_fmt == "JPG":
                final_img = generated_img.convert("RGB")
                final_img.save(save_path, format="JPEG", quality=95)
            else:
                generated_img.save(save_path, format="PNG")

            # Save Log if requested
            if config.get('save_log', False):
                 log_text = f"PROMPT:\n{prompt_data['prompt']}"
                 (image_out_dir / f"{base_name}.txt").write_text(log_text, encoding="utf-8")

            return {
                'success': True,
                'saved_path': save_path,
                'is_diff_resolution': is_diff,
                'ratio': f"{gen_w}:{gen_h}" # simplified for log 
            }

        except Exception as e:
            return {'success': False, 'error': f"Save failed: {e}"}
