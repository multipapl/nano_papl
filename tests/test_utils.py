import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils import image_utils, prompt_parser, resource_helper

class TestUtils(unittest.TestCase):
    
    # --- Image Utils Tests ---
    def test_get_smart_ratio(self):
        # Mocking Image.open is complex because it returns a context manager
        # easier to create a dummy image or mock the context manager
        with patch("utils.image_utils.Image.open") as mock_open:
            # Setup mock
            mock_img = MagicMock()
            mock_img.size = (1920, 1080) # 16:9
            mock_open.return_value.__enter__.return_value = mock_img
            
            ratio = image_utils.get_smart_ratio("dummy.png")
            self.assertEqual(ratio, "16:9")
            
            # Test 1:1
            mock_img.size = (1024, 1024)
            ratio = image_utils.get_smart_ratio("dummy.png")
            self.assertEqual(ratio, "1:1")
            
            # Test slightly off 4:3 (e.g. 800x600 is exact, 802x600 is close)
            # 800/600 = 1.333 | 4/3 = 1.333
            mock_img.size = (802, 600) 
            ratio = image_utils.get_smart_ratio("dummy.png")
            self.assertEqual(ratio, "4:3")

    # --- Prompt Parser Tests ---
    def test_parse_markdown_prompts(self):
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value="### Test_Title\nThis is a prompt."):
             
            data = prompt_parser.parse_markdown_prompts("path/to/prompts.md")
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["title"], "Test_Title")
            self.assertEqual(data[0]["prompt"], "This is a prompt.")

    def test_parse_markdown_multiple(self):
        content = """
### Scene_1
A beautiful sunset.
### Scene 2
A dark forest.
"""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value=content):
             
            data = prompt_parser.parse_markdown_prompts("foo.md")
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["title"], "Scene_1")
            self.assertEqual(data[0]["prompt"], "A beautiful sunset.")
            self.assertEqual(data[1]["title"], "Scene_2") # Space replaced by _
            self.assertEqual(data[1]["prompt"], "A dark forest.")

    # --- Resource Helper Tests ---
    def test_get_resource_path_dev(self):
        # Test normal dev environment (no _MEIPASS)
        # Ensure _MEIPASS is not present (it shouldn't be in standard dev run)
        if hasattr(sys, '_MEIPASS'):
            del sys._MEIPASS
            
        path = resource_helper.get_resource_path("assets/icon.png")
        # Should be absolute path containing assets/icon.png
        self.assertTrue("assets" in path)
        self.assertTrue(os.path.isabs(path))

    def test_get_resource_path_pyinstaller(self):
        with patch.object(sys, '_MEIPASS', "/tmp/MEI1234", create=True):
            path = resource_helper.get_resource_path("config.json")
            # Should be joined path
            expected = os.path.join("/tmp/MEI1234", "config.json")
            self.assertEqual(path, expected)

if __name__ == '__main__':
    unittest.main()
