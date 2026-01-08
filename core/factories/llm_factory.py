from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image
import google.genai as genai
from google.genai import types
from core.utils import image_utils

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
                mime = image_utils.get_mime_type(p)
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
        # Aspect ratio calculation already uses image_utils.get_smart_ratio
        if aspect_ratio.lower() == "auto" and image_paths:
             try:
                aspect_ratio = image_utils.get_smart_ratio(image_paths[0])
             except:
                aspect_ratio = "16:9"
        
        # Check if model supports image generation
        is_flash_model = "flash" in self.model_id.lower()
        # You might want a better way to classify, but adhering to the specific error:
        # gemini-3-flash-preview is text/multimodal-input but NOT image-output
        
        gen_config_args = {
            "temperature": 0.7,
            "system_instruction": system_instruction
        }

        if is_flash_model:
            # TEXT ONLY OUTPUT
            gen_config_args["response_modalities"] = ["TEXT"]
            # Do NOT pass image_config
        else:
            # TEXT + IMAGE OUTPUT
            image_config_params = {"image_size": resolution}
            if aspect_ratio.lower() != "auto":
                image_config_params["aspect_ratio"] = aspect_ratio
            
            gen_config_args["response_modalities"] = ["TEXT", "IMAGE"]
            gen_config_args["image_config"] = types.ImageConfig(**image_config_params)

        gen_config = types.GenerateContentConfig(**gen_config_args)

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
