import pytest
import shutil
from pathlib import Path
from core.history_manager import HistoryManager

# Fixture to provide a temporary directory for tests
@pytest.fixture
def temp_history_dir(tmp_path):
    d = tmp_path / "test_history"
    d.mkdir()
    return d

def test_session_creation(temp_history_dir):
    """Test that creating a session creates a file and returns ID."""
    hm = HistoryManager(base_dir=temp_history_dir)
    sid, data = hm.create_session()
    
    assert sid is not None
    assert "messages" in data
    assert (temp_history_dir / f"{sid}.json").exists()

def test_list_sessions(temp_history_dir):
    """Test creating multiple sessions and listing them."""
    hm = HistoryManager(base_dir=temp_history_dir)
    hm.create_session()
    hm.create_session()
    
    sessions = hm.list_sessions()
    assert len(sessions) == 2

def test_save_and_load(temp_history_dir):
    """Test saving a message and reloading it."""
    hm = HistoryManager(base_dir=temp_history_dir)
    sid, data = hm.create_session()
    
    data["messages"].append({"role": "user", "text": "Hello Test"})
    hm.save_session(sid, data)
    
    # Reload
    loaded_data = hm.load_session(sid)
    assert len(loaded_data["messages"]) == 1
    assert loaded_data["messages"][0]["text"] == "Hello Test"

def test_delete_session(temp_history_dir):
    """Test deleting a session."""
    hm = HistoryManager(base_dir=temp_history_dir)
    sid, _ = hm.create_session()
    
    assert (temp_history_dir / f"{sid}.json").exists()
    
    hm.delete_session(sid)
    
    assert not (temp_history_dir / f"{sid}.json").exists()
