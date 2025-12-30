from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image
import io

class LLMClient:
    def __init__(self, provider, model_id, api_key=None):
        self.provider = "gemini" # Force override
        self.model_id = "gemini-3-pro-image-preview" 
        self.api_key = api_key
        
        # Init Google Client
        if self.api_key:
            self.google_client = genai.Client(api_key=self.api_key)
        else:
            self.google_client = None

    def generate_chat(self, history_messages, new_text, image_paths=[], system_instruction="", resolution="1K", ratio="1:1"):
        """
        Gemini Only Generation.
        Returns: (text_response, generated_image_bytes_or_none)
        """
        return self._generate_gemini(history_messages, new_text, image_paths, system_instruction, resolution, ratio)

    def _generate_gemini(self, history, prompt, image_paths, system_instruction, resolution="1K", ratio="1:1"):
        if not self.google_client:
            return "Error: Gemini API Key missing. Please check Settings.", None
            
        # Current User Content
        current_parts = [types.Part.from_text(text=prompt)]
        for path in image_paths:
            p = Path(path)
            if p.exists():
                img_data = p.read_bytes()
                mime = "image/png"
                if p.suffix.lower() in ['.jpg', '.jpeg']: mime = "image/jpeg"
                if p.suffix.lower() == '.webp': mime = "image/webp"
                current_parts.append(types.Part.from_bytes(data=img_data, mime_type=mime))
        
        # Constructing Google History Objects
        google_history = []
        for msg in history:
            role = "model" if msg["role"] == "model" else "user"
            parts = [types.Part.from_text(text=msg.get("text", ""))]
            google_history.append(types.Content(role=role, parts=parts))

        # Native handle for Gemini (Bucket-Perfect Detection)
        ar_param = ratio
        if ar_param.lower() == "auto" and image_paths:
            # Detect ratio from the first image
            try:
                with Image.open(image_paths[0]) as img:
                    w, h = img.size
                    curr_ratio = w / h
                    common = [
                        (1, 1), (16, 9), (9, 16), (4, 3), (3, 4), 
                        (3, 2), (2, 3), (5, 4), (4, 5), (21, 9)
                    ]
                    best = min(common, key=lambda r: abs(curr_ratio - r[0]/r[1]))
                    ar_param = f"{best[0]}:{best[1]}"
            except:
                ar_param = "16:9" # Fallback

        image_config_params = {"image_size": resolution}
        if ar_param.lower() != "auto":
            image_config_params["aspect_ratio"] = ar_param

        # Config with Official ImageConfig
        gen_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(**image_config_params)
        )

        chat = self.google_client.chats.create(
            model=self.model_id,
            config=gen_config,
            history=google_history
        )
        
        try:
            response = chat.send_message(current_parts)
            
            text_out = ""
            img_bytes = None
            
            if response.parts:
                for part in response.parts:
                    if part.text: text_out += part.text + "\n"
                    if part.inline_data: img_bytes = part.inline_data.data
            
            return text_out.strip(), img_bytes
            
        except Exception as e:
            return f"Gemini Error: {e}", None
