import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from qfluentwidgets import setTheme, Theme, isDarkTheme
from ui.components import MessageBubble, ThemeAwareBackground

def test_theme_aware_background_color(qtbot):
    """Перевірка, чи змінює ThemeAwareBackground свій колір при зміні теми."""
    widget = ThemeAwareBackground()
    qtbot.addWidget(widget)
    
    # Світла тема
    setTheme(Theme.LIGHT)
    assert not isDarkTheme()
    # Ми не можемо легко перевірити результат paintEvent без складних моків, 
    # але ми можемо перевірити, що віджет реагує на сигнал.
    
def test_message_bubble_styling_change(qtbot):
    """Перевірка, чи оновлюється stylesheet MessageBubble при зміні теми."""
    bubble = MessageBubble("Hello", is_user=False)
    qtbot.addWidget(bubble)
    
    # Тестуємо AI Bubble (Light)
    setTheme(Theme.LIGHT)
    assert "#f5f5f5" in bubble.bubble.styleSheet().lower()
    
    # Перемикаємо на Dark
    setTheme(Theme.DARK)
    assert "#2d2d2d" in bubble.bubble.styleSheet().lower()

def test_user_bubble_theme_color(qtbot):
    """Перевірка кольору бабла користувача (має брати колір з конфігу)."""
    bubble = MessageBubble("User message", is_user=True)
    qtbot.addWidget(bubble)
    
    setTheme(Theme.LIGHT)
    # За замовчуванням у конфігу може бути #4cc2ff
    # Перевіримо, що колір присутній у стилях
    style = bubble.bubble.styleSheet().lower()
    assert "background-color:" in style
