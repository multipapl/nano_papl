import pytest
from PySide6.QtCore import Qt
from ui.widgets.chat.sidebar import ChatSidebar

@pytest.fixture
def sidebar(qtbot):
    """Створює віджет сайдбару для тестів."""
    sb = ChatSidebar()
    qtbot.addWidget(sb)
    return sb

def test_sidebar_initialization(sidebar):
    """Перевірка початкового стану сайдбару."""
    assert sidebar.history_list.topLevelItemCount() == 0
    assert sidebar.btn_new.text() == "New Chat"

def test_sidebar_populate_sessions(sidebar):
    """Перевірка заповнення дерева сесій."""
    mock_structure = {
        "folders": {
            "Work": [
                {"id": "s1", "title": "Session 1", "updated_at": "2024-01-01", "folder": "Work"}
            ]
        },
        "sessions": [
            {"id": "s2", "title": "Session 2", "updated_at": "2024-01-01", "folder": ""}
        ]
    }
    
    sidebar.set_sessions(mock_structure)
    
    # 2 Top level items: folder "Work" and session "Session 2"
    assert sidebar.history_list.topLevelItemCount() == 2
    
    # Check folder item
    folder_item = sidebar.history_list.topLevelItem(0)
    assert folder_item.text(0) == "Work"
    assert folder_item.childCount() == 1
    assert folder_item.child(0).text(0) == "Session 1"

def test_sidebar_signals(qtbot, sidebar):
    """Перевірка сигналів при кліку на сесію."""
    mock_structure = {
        "folders": {},
        "sessions": [{"id": "s-test", "title": "Test Session", "updated_at": "", "folder": ""}]
    }
    sidebar.set_sessions(mock_structure)
    item = sidebar.history_list.topLevelItem(0)
    
    with qtbot.waitSignal(sidebar.sessionSelected) as blocker:
        sidebar._on_item_clicked(item)
    
    assert blocker.args == ["s-test"]
