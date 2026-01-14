import os
import pytest
from core.history_manager import HistoryManager

@pytest.fixture
def history_manager(tmp_path):
    """Створює HistoryManager з використанням тимчасової папки."""
    return HistoryManager(base_dir=tmp_path)

def test_create_session(history_manager):
    """Тест створення нової сесії."""
    session_id, data = history_manager.create_session()
    
    assert session_id is not None
    assert data["title"] == "New Chat"
    assert os.path.exists(history_manager._get_path(session_id))

def test_save_and_load_session(history_manager):
    """Тест збереження та завантаження сесії."""
    session_id, data = history_manager.create_session()
    data["title"] = "Updated Title"
    data["messages"].append({"role": "user", "text": "Test message"})
    
    history_manager.save_session(session_id, data)
    
    loaded_data = history_manager.load_session(session_id)
    assert loaded_data is not None
    assert loaded_data["title"] == "Updated Title"
    assert len(loaded_data["messages"]) == 1

def test_delete_session(history_manager):
    """Тест видалення сесії."""
    session_id, _ = history_manager.create_session()
    path = history_manager._get_path(session_id)
    assert os.path.exists(path)
    
    history_manager.delete_session(session_id)
    assert not os.path.exists(path)

def test_create_folder(history_manager):
    """Тест створення папки для історій."""
    folder_name = "Work"
    history_manager.create_folder(folder_name)
    folder_path = history_manager.base_dir / folder_name
    assert folder_path.exists()
    assert folder_path.is_dir()
