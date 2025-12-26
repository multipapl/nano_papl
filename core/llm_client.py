from pathlib import Path
from google import genai
from google.genai import types

class LLMClient:
    def __init__(self, provider, model_id, api_key=None):
        self.provider = "gemini" # Force override
        self.model_id = "gemini-3-pro-image-preview" # Updated to latest per user request
        self.api_key = api_key
        
        # Init Google Client
        if self.api_key:
            self.google_client = genai.Client(api_key=self.api_key)
        else:
            self.google_client = None

    def generate_chat(self, history_messages, new_text, image_paths=[], system_instruction="", settings_text=""):
        """
        Gemini Only Generation.
        Returns: (text_response, generated_image_bytes_or_none)
        """
        full_prompt = new_text
        if settings_text:
            full_prompt += f"\n\n{settings_text}"
            
        return self._generate_gemini(history_messages, full_prompt, image_paths, system_instruction)

    def _generate_gemini(self, history, prompt, image_paths, system_instruction):
        if not self.google_client:
            return "Error: Gemini API Key missing. Please check Settings.", None
            
        contents = []
        for path in image_paths:
            p = Path(path)
            if p.exists():
                img_data = p.read_bytes()
                mime = "image/png"
                if p.suffix.lower() in ['.jpg', '.jpeg']: mime = "image/jpeg"
                if p.suffix.lower() == '.webp': mime = "image/webp"
                contents.append(types.Part.from_bytes(data=img_data, mime_type=mime))
        
        contents.append(prompt)
        
        # Constructing Google History Objects from dicts:
        google_history = []
        for msg in history:
            role = "model" if msg["role"] == "model" else "user"
            parts = [types.Part(text=msg.get("text", ""))]
            google_history.append(types.Content(role=role, parts=parts))

        chat = self.google_client.chats.create(
            model=self.model_id,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                response_modalities=["TEXT", "IMAGE"]
            ),
            history=google_history
        )
        
        try:
            response = chat.send_message(contents)
            
            text_out = ""
            img_bytes = None
            
            if response.parts:
                for part in response.parts:
                    if part.text: text_out += part.text + "\n"
                    if part.inline_data: img_bytes = part.inline_data.data
            
            return text_out.strip(), img_bytes
            
        except Exception as e:
            return f"Gemini Error: {e}", None
