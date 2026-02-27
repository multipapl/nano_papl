import pytest
from PySide6.QtCore import Qt
from ui.components import NPButton, MessageBubble, ChatTextEdit

def test_np_button_creation(qtbot):
    """Перевірка створення кнопки через фабрику NPButton."""
    btn = NPButton("Test Button", is_primary=True)
    qtbot.addWidget(btn)
    
    assert btn.text() == "Test Button"
    assert btn.cursor().shape() == Qt.PointingHandCursor

def test_message_bubble_user(qtbot):
    """Перевірка створення бабла повідомлення користувача."""
    text = "Hello from user"
    bubble = MessageBubble(text, is_user=True)
    qtbot.addWidget(bubble)
    
    assert bubble.bubble.text() == text
    assert bubble.is_user is True

def test_message_bubble_ai(qtbot):
    """Перевірка створення бабла повідомлення ШІ."""
    text = "Hello from AI"
    bubble = MessageBubble(text, is_user=False)
    qtbot.addWidget(bubble)
    
    assert bubble.bubble.text() == text
    assert bubble.is_user is False
    assert bubble.avatar is not None

def test_chat_text_edit_height_expansion(qtbot):
    """Перевірка авто-розширення висоти текстового поля."""
    edit = ChatTextEdit()
    qtbot.addWidget(edit)
    
    initial_height = edit.height()
    
    # Додаємо багато тексту
    edit.setPlainText("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6")
    
    # Висота повинна збільшитись (але не більше max_height=200)
    assert edit.height() > initial_height
    assert edit.height() <= 200
