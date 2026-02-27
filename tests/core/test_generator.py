import pytest
from core.generator import PromptGenerator

@pytest.fixture
def base_settings():
    return {
        "project_name": "TestProj",
        "base_text": "Base text",
        "context": "Context",
        "global_rules": "Rules",
        "camera": "Cam",
        "xmas_desc": "Xmas",
        "active_seasons": {}
    }

def test_generate_empty(base_settings):
    """Verify generator output with no active seasons."""
    gen = PromptGenerator()
    content = gen.generate_markdown(base_settings)
    assert content.strip() == "### TestProj"

def test_generate_single_season(base_settings):
    """Verify generator output with one active season and light."""
    gen = PromptGenerator()
    settings = base_settings.copy()
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
    content = gen.generate_markdown(settings)
    assert "### TestProj" in content
    assert "### Summer + Daylight" in content
    assert "Summer time" in content
    assert "Sunny" in content
    assert "Bright sun" in content

def test_generate_xmas_variant(base_settings):
    """Verify Xmas specific description integration."""
    gen = PromptGenerator()
    settings = base_settings.copy()
    settings["active_seasons"] = {
        "Winter": {
            "is_active": True,
            "season_text": "Snowy",
            "atmos": "Cold",
            "lights": {
                "Night": {
                    "is_active": True,
                    "desc": "Dark",
                    "is_xmas": True
                }
            }
        }
    }
    content = gen.generate_markdown(settings)
    assert "### Winter + Night + Xmas" in content
    assert "Cold Xmas" in content or "Cold. Xmas" in content # depends on generator logic
