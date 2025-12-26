import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from utils import config_helper

class TestLLMClient(unittest.TestCase):
    @patch('core.llm_client.genai.Client')
    def test_init_gemini(self, mock_client_cls):
        api_key = "test_key"
        client = LLMClient("gemini", "model_id", api_key)
        
        # Verify it ignores provider/model args and hardcodes gemini
        self.assertEqual(client.provider, "gemini")
        self.assertEqual(client.model_id, "gemini-3-pro-image-preview")
        self.assertEqual(client.api_key, api_key)
        
        # Verify Google Client was initialized
        mock_client_cls.assert_called_with(api_key=api_key)

    @patch('core.llm_client.genai.Client')
    def test_generate_gemini_success(self, mock_client_cls):
        # Setup Mock
        mock_instance = mock_client_cls.return_value
        mock_chat = MagicMock()
        mock_instance.chats.create.return_value = mock_chat
        
        # Mock Response
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Hello World"
        mock_part.inline_data = None
        mock_response.parts = [mock_part]
        mock_chat.send_message.return_value = mock_response
        
        client = LLMClient("gemini", "mod", "key")
        
        history = [{"role": "user", "text": "Hi"}]
        text, img = client.generate_chat(history, "Hello")
        
        self.assertEqual(text, "Hello World\n".strip())
        self.assertIsNone(img)

class TestConfigHelper(unittest.TestCase):
    @patch("utils.config_helper.keyring")
    @patch("builtins.open", new_callable=mock_open, read_data='{"data_root": "C:/Test"}')
    @patch("os.path.exists", return_value=True)
    def test_load_config(self, mock_exists, mock_file, mock_keyring):
        # Setup Keyring Mock
        mock_keyring.get_password.return_value = "secret_key"
        
        # Test Get Value for normal key
        path = config_helper.get_value("data_root")
        self.assertEqual(path, "C:/Test")
        
        # Test Get Value for api_key
        key = config_helper.get_value("api_key")
        self.assertEqual(key, "secret_key")

    @patch("utils.config_helper.keyring")
    @patch("utils.config_helper.save_config") # Don't actually write file
    @patch("utils.config_helper.load_config") # Return dummy dict
    def test_set_value_api_key(self, mock_load, mock_save, mock_keyring):
        mock_load.return_value = {}
        
        config_helper.set_value("api_key", "new_key")
        
        # Verify it calls keyring
        mock_keyring.set_password.assert_called_with("NanoPapl", "api_key", "new_key")
        # Verify it DOES NOT save to config file (save_config is called only if key existed in json)
        mock_save.assert_not_called()

if __name__ == '__main__':
    unittest.main()
