import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QWidget
from ui.base_tab import BaseTab
from ui.widgets.stateful_widget import StatefulWidget

# Mock Widget implementing StatefulWidget
class MockStateWidget(StatefulWidget):
    def __init__(self):
        super().__init__()
        self.state = ""
    
    def get_state(self):
        return self.state
    
    def set_state(self, value):
        self.state = value

# Mock Tab inheriting BaseTab
class MockTab(BaseTab):
    def __init__(self):
        super().__init__()
        self.widget1 = MockStateWidget()
        self.register_field("key1", self.widget1)

@pytest.fixture
def app(qtbot):
    """Fixture to ensure QApplication exists."""
    return qtbot

def test_base_tab_register(app):
    """Test field registration."""
    tab = MockTab()
    assert "key1" in tab.field_registry
    assert tab.field_registry["key1"] == tab.widget1

@patch("ui.base_tab.config_helper")
def test_save_state(mock_config, app):
    """Test saving state calls config_helper."""
    # Setup
    mock_config.load_config.return_value = {}
    
    tab = MockTab()
    tab.widget1.set_state("my_value")
    
    # Action
    tab.save_state()
    
    # Verify
    mock_config.save_config.assert_called_once()
    saved_data = mock_config.save_config.call_args[0][0]
    assert saved_data["key1"] == "my_value"

@patch("ui.base_tab.config_helper")
def test_load_state(mock_config, app):
    """Test loading state populates widgets."""
    # Setup
    mock_config.load_config.return_value = {"key1": "loaded_value"}
    
    tab = MockTab()
    # Initial state empty
    assert tab.widget1.get_state() == ""
    
    # Action
    tab.load_state()
    
    # Verify
    assert tab.widget1.get_state() == "loaded_value"

def test_autosave_timer(qtbot):
    """Test autosave timer triggers save."""
    with patch("ui.base_tab.config_helper") as mock_config:
        mock_config.load_config.return_value = {}
        
        tab = MockTab()
        tab.enable_autosave(delay_ms=100)
        
        # Trigger modification (manually emitting signal for test)
        # Note: MockStateWidget didn't emit modified, let's pretend
        tab.save_state = MagicMock()
        
        # Simulate signal
        tab._queue_autosave()
        
        # Should not be called immediately
        tab.save_state.assert_not_called()
        
        # Wait for timer
        qtbot.wait(150)
        
        # Should be called now
        tab.save_state.assert_called_once()
