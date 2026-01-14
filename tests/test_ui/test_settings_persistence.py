import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from ui.widgets.chat.input_area import ChatInputArea
from core.utils import config_helper


@pytest.fixture
def app(qtbot):
    """Fixture to ensure QApplication exists."""
    return qtbot


def test_chat_input_config_persistence(app):
    """Test that ChatInputArea saves and loads settings correctly"""
    
    # Create input area
    input_area = ChatInputArea()
    
    # Set some configuration
    test_config = {
        "model_index": 1,
        "ratio_index": 2,
        "res_index": 0,
        "img_mode": False
    }
    
    input_area.set_chat_config(test_config)
    
    # Verify the configuration was applied
    current_config = input_area.get_chat_config()
    
    assert current_config["model_index"] == 1
    assert current_config["ratio_index"] == 2
    assert current_config["res_index"] == 0
    assert current_config["img_mode"] == False
    
    print("✓ Settings persistence test passed")


def test_chat_input_image_mode_toggle(app):
    """Test that image mode toggle correctly enables/disables controls"""
    
    input_area = ChatInputArea()
    
    # Initially image mode should be enabled
    assert input_area.chk_img_mode.isChecked() == True
    assert input_area.cbox_ratio.isEnabled() == True
    assert input_area.cbox_res.isEnabled() == True
    
    # Disable image mode
    input_area.chk_img_mode.setChecked(False)
    QApplication.processEvents()
    
    # Verify controls are disabled
    assert input_area.cbox_ratio.isEnabled() == False
    assert input_area.cbox_res.isEnabled() == False
    
    print("✓ Image mode toggle test passed")


def test_chat_input_signals(app, qtbot):
    """Test that ChatInputArea emits correct signals"""
    
    input_area = ChatInputArea()
    
    # Create signal spy for sendClicked
    with qtbot.waitSignal(input_area.sendClicked, timeout=1000) as blocker:
        input_area.input_box.setPlainText("Test message")
        input_area.btn_send.click()
    
    # Verify signal was emitted with correct data
    text, config = blocker.args
    assert text == "Test message"
    assert isinstance(config, dict)
    assert "model" in config
    assert "ratio" in config
    assert "res" in config
    
    print("✓ Signal emission test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
