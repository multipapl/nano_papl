import pytest
from PySide6.QtCore import Qt, QTimer
from ui.pages.chat_page import ChatInterface
from core.history_manager import HistoryManager

@pytest.fixture
def chat_interface(qtbot, tmp_path):
    """Створює ChatInterface для тестів."""
    from core.utils import config_helper
    hm = HistoryManager(base_dir=tmp_path)
    
    # Use real config_manager but point data_root to tmp_path
    config_helper.config_manager.config.data_root = str(tmp_path)
    
    interface = ChatInterface(hm, config_helper.config_manager)
    qtbot.addWidget(interface)
    interface.show() # Ensure widget is considered 'visible' for state checks
    return interface

def test_chat_interface_initialization(chat_interface):
    """Перевірка ініціалізації чату та завантаження першої сесії."""
    assert chat_interface.objectName() == "ChatInterface"
    assert chat_interface.current_session_id is not None
    # Має бути хоча б одне привітальне повідомлення
    assert chat_interface.message_display.message_count() >= 1

def test_send_message_updates_ui(qtbot, chat_interface, monkeypatch):
    """Центральний тест: перевірка, що повідомлення додається в UI."""
    # Мокаємо ChatWorker, щоб він не запускав реальний потік і не робив запитів
    from PySide6.QtCore import QObject, Signal
    class MockWorker(QObject):
        response_signal = Signal(object) # Now object per BaseWorker
        error_signal = Signal(str)
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.user_message = args[3] if len(args) > 3 else ""
            self.session_id = args[5] if len(args) > 5 else None
        def start(self): pass
        def isRunning(self): return False
        
    # Provide a mock API key to avoid "API Key missing" error message in UI
    chat_interface.config_manager.config.api_key = "mock-key"
    
    msg_count_before = chat_interface.message_display.message_count()
    test_text = "Test user message"
    
    # Вводимо текст
    chat_interface.control_panel.input_area.input_box.setPlainText(test_text)
    
    # Симулюємо клік на кнопку відправити
    qtbot.mouseClick(chat_interface.control_panel.input_area.btn_send, Qt.LeftButton)
    
    # Перевіряємо, що в UI з'явилось нове повідомлення
    assert chat_interface.message_display.message_count() == msg_count_before + 1
    
    # Перевіряємо, що в історії (HistoryManager) теж з'явилось повідомлення
    session = chat_interface.history_manager.load_session(chat_interface.current_session_id)
    assert any(m["text"] == test_text for m in session["messages"])

def test_toggle_sidebar(qtbot, chat_interface):
    """Перевірка приховання/показу сайдбару."""
    # Перевіряємо через властивість, а не isVisible(), бо у тестах вікно може бути не 'активним' на екрані
    initial_hidden = chat_interface.chat_sidebar.isHidden()
    chat_interface.toggle_sidebar()
    assert chat_interface.chat_sidebar.isHidden() != initial_hidden
