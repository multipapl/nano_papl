import pytest
from unittest.mock import MagicMock, patch
from core.llm_client import LLMClient

@patch('core.llm_client.LLMProviderFactory')
def test_llm_client_initialization(mock_factory):
    """Verify LLMClient correctly initializes the provider via factory."""
    mock_provider = MagicMock()
    mock_factory.get_provider.return_value = mock_provider
    
    client = LLMClient("google", "gemini-pro", "test-key")
    
    mock_factory.get_provider.assert_called_with("google", "test-key", "gemini-pro")
    assert client.provider == mock_provider

@patch('core.llm_client.LLMProviderFactory')
def test_llm_client_generate_call(mock_factory):
    """Verify LLMClient delegates generation to the provider with correct arguments."""
    mock_provider = MagicMock()
    mock_factory.get_provider.return_value = mock_provider
    mock_provider.generate_chat.return_value = ("AI Response", "path/to/img.png")
    
    client = LLMClient("google", "mod", "key")
    history = [{"role": "user", "text": "Hi"}]
    
    # LLMClient.generate_chat signature: (history, new_text, image_paths=[], system_instruction="", resolution="1K", ratio="1:1")
    text, img = client.generate_chat(history, "Hello", resolution="2K")
    
    # Implementation constructs a config dict for the provider
    expected_config = {"resolution": "2K", "ratio": "1:1"}
    # Actual call to provider: generate_chat(history, new_text, image_paths, system_instruction, config)
    mock_provider.generate_chat.assert_called_once_with(history, "Hello", [], "", expected_config)
    
    assert text == "AI Response"
    assert img == "path/to/img.png"
