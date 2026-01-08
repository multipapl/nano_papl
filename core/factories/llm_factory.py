from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image
import google.genai as genai
from google.genai import types

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    @abstractmethod
    def generate_chat(self, history: list, message: str, image_paths: list, system_instruction: str, config: dict):
        pass

class GeminiProvider(LLMProvider):
    """Gemini implementation of LLMProvider."""
    def __init__(self, api_key, model_id):
        self.api_key = api_key
        self.model_id = model_id
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_chat(self, history, message, image_paths, system_instruction, config):
        if not self.client:
            return "Error: Gemini API Key missing.", None

        # 1. Prepare User Content
        current_parts = [types.Part.from_text(text=message)]
        for path in image_paths:
            p = Path(path)
            if p.exists():
                img_data = p.read_bytes()
                mime = "image/png"
                if p.suffix.lower() in ['.jpg', '.jpeg']: mime = "image/jpeg"
                if p.suffix.lower() == '.webp': mime = "image/webp"
                current_parts.append(types.Part.from_bytes(data=img_data, mime_type=mime))

        # 2. History Conversion
        google_history = []
        for msg in history:
            role = "model" if msg["role"] == "model" else "user"
            parts = [types.Part.from_text(text=msg.get("text", ""))]
            google_history.append(types.Content(role=role, parts=parts))

        # 3. Config (Ratio Logic)
        resolution = config.get("resolution", "1K")
        aspect_ratio = config.get("ratio", "1:1")
        
        # Auto Ratio Logic
        if aspect_ratio.lower() == "auto" and image_paths:
             try:
                with Image.open(image_paths[0]) as img:
                    w, h = img.size
                    curr_ratio = w / h
                    common = [
                        (1, 1), (16, 9), (9, 16), (4, 3), (3, 4), 
                        (3, 2), (2, 3), (5, 4), (4, 5), (21, 9)
                    ]
                    best = min(common, key=lambda r: abs(curr_ratio - r[0]/r[1]))
                    aspect_ratio = f"{best[0]}:{best[1]}"
             except:
                aspect_ratio = "16:9"

        image_config_params = {"image_size": resolution}
        if aspect_ratio.lower() != "auto":
            image_config_params["aspect_ratio"] = aspect_ratio

        gen_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(**image_config_params)
        )

        # 4. Chat Creation & Sending
        chat = self.client.chats.create(
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

class LLMProviderFactory:
    """Factory to create LLM Providers."""
    @staticmethod
    def get_provider(provider_name, api_key, model_id):
        if provider_name.lower() == "gemini":
            return GeminiProvider(api_key, model_id)
        # Placeholder for future providers
        # if provider_name.lower() == "claude": ...
        
        # Fallback or Error
        raise ValueError(f"Unknown provider: {provider_name}")
