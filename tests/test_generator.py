import unittest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from core.generator import PromptGenerator

class TestPromptGenerator(unittest.TestCase):
    def setUp(self):
        self.gen = PromptGenerator()
        self.base_settings = {
            "project_name": "TestProj",
            "base_text": "Base text",
            "context": "Context",
            "global_rules": "Rules",
            "camera": "Cam",
            "xmas_desc": "Xmas",
            "active_seasons": {}
        }

    def test_generate_empty(self):
        content = self.gen.generate_markdown(self.base_settings)
        # Should only contain project header
        self.assertEqual(content.strip(), "### TestProj")

    def test_generate_single_season_light(self):
        settings = self.base_settings.copy()
        settings["active_seasons"] = {
            "Summer": {
                "is_active": True,
                "season_text": "Summer time",
                "atmos": "Sunny",
                "lights": {
                    "Daylight": {
                        "is_active": True,
                        "desc": "Bright sun",
                        "is_xmas": False
                    }
                }
            }
        }
        content = self.gen.generate_markdown(settings)
        self.assertIn("### TestProj", content)
        self.assertIn("### Summer + Daylight", content)
        self.assertIn("Summer time", content)
        self.assertIn("Sunny", content)
        self.assertIn("Bright sun", content)

    def test_generate_xmas_variant(self):
        settings = self.base_settings.copy()
        settings["active_seasons"] = {
            "Winter": {
                "is_active": True,
                "season_text": "Winter time",
                "atmos": "Cold.",
                "lights": {
                    "Night": {
                        "is_active": True,
                        "desc": "Dark",
                        "is_xmas": True
                    }
                }
            }
        }
        content = self.gen.generate_markdown(settings)
        self.assertIn("### Winter + Night + Xmas", content)
        self.assertIn("Cold. Xmas", content)

if __name__ == "__main__":
    unittest.main()
