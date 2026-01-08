from core.factories.llm_factory import LLMProviderFactory

class LLMClient:
    """
    Client for interacting with LLM Providers.
    Uses Factory pattern to select the backend (Gemini, Claude, etc.).
    """
    def __init__(self, provider_name, model_id, api_key=None):
        self.provider = LLMProviderFactory.get_provider(provider_name, api_key, model_id)

    def generate_chat(self, history_messages, new_text, image_paths=[], system_instruction="", resolution="1K", ratio="1:1"):
        """
        Generic generation method exposed to Workers.
        """
        config = {
            "resolution": resolution,
            "ratio": ratio
        }
        return self.provider.generate_chat(
            history_messages, 
            new_text, 
            image_paths, 
            system_instruction, 
            config
        )
