import pytest
from unittest.mock import MagicMock, patch
from core.factories.llm_factory import LLMProviderFactory, GeminiProvider

def test_get_gemini_provider():
    """Test factory returns GeminiProvider."""
    provider = LLMProviderFactory.get_provider("gemini", "my_key", "my_model")
    assert isinstance(provider, GeminiProvider)
    assert provider.api_key == "my_key"
    assert provider.model_id == "my_model"

def test_get_unknown_provider():
    """Test factory raises error for unknown provider."""
    with pytest.raises(ValueError) as excinfo:
        LLMProviderFactory.get_provider("unknown_provider", "key", "model")
    assert "Unknown provider" in str(excinfo.value)

@patch('core.factories.llm_factory.genai.Client')
def test_gemini_provider_init(mock_client_cls):
    """Test GeminiProvider initializes Client."""
    provider = GeminiProvider("test_key", "test_model")
    assert provider.client is not None
    mock_client_cls.assert_called_with(api_key="test_key")

def test_gemini_provider_no_key():
    """Test GeminiProvider handles missing key."""
    provider = GeminiProvider(None, "test_model")
    assert provider.client is None
    
    # Generate should return error
    text, img = provider.generate_chat([], "hi", [], "", {})
    assert "Key missing" in text
