import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.utils import config_helper

class TestLLMClient(unittest.TestCase):
    @patch('core.llm_client.LLMProviderFactory')
    def test_init_gemini(self, mock_factory):
        # Setup mock provider
        mock_provider = MagicMock()
        mock_factory.get_provider.return_value = mock_provider
        
        api_key = "test_key"
        # Init client
        client = LLMClient("gemini", "model_id", api_key)
        
        # Verify Factory was called with correct args
        mock_factory.get_provider.assert_called_with("gemini", api_key, "model_id")
        
        # Verify client holds the provider
        self.assertEqual(client.provider, mock_provider)

    @patch('core.llm_client.LLMProviderFactory')
    def test_generate_delegation(self, mock_factory):
        # Setup Mock Provider
        mock_provider = MagicMock()
        mock_factory.get_provider.return_value = mock_provider
        
        # Setup Mock Response
        mock_provider.generate_chat.return_value = ("Hello World", None)
        
        client = LLMClient("gemini", "mod", "key")
        
        history = [{"role": "user", "text": "Hi"}]
        text, img = client.generate_chat(history, "Hello")
        
        # Verify generate_chat was called on provider
        mock_provider.generate_chat.assert_called_once()
        
        # Verify return values
        self.assertEqual(text, "Hello World")
        self.assertIsNone(img)

class TestConfigHelper(unittest.TestCase):
    @patch("core.utils.config_helper.keyring")
    @patch("builtins.open")
    @patch("os.path.exists", return_value=True)
    def test_load_config(self, mock_exists, mock_file, mock_keyring):
        # Mock file read
        mock_file.return_value.__enter__.return_value.read.return_value = '{"data_root": "C:/Test"}'
        
        # Setup Keyring Mock
        mock_keyring.get_password.return_value = "secret_key"
        
        # Test Get Value for normal key
        path = config_helper.get_value("data_root")
        self.assertEqual(path, "C:/Test")
        
        # Test Get Value for api_key
        key = config_helper.get_value("api_key")
        self.assertEqual(key, "secret_key")

    @patch("core.utils.config_helper.keyring")
    @patch("core.utils.config_helper.save_config") # Don't actually write file
    @patch("core.utils.config_helper.load_config") # Return dummy dict
    def test_set_value_api_key(self, mock_load, mock_save, mock_keyring):
        mock_load.return_value = {}
        
        config_helper.set_value("api_key", "new_key")
        
        # Verify it calls keyring
        mock_keyring.set_password.assert_called_with("NanoPapl", "api_key", "new_key")
        # Verify it DOES NOT save to config file (save_config is called only if key existed in json)
        mock_save.assert_not_called()

if __name__ == '__main__':
    unittest.main()
