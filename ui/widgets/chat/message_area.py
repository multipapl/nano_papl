from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QSizePolicy
from PySide6.QtCore import Qt, QTimer

from ui.components import MessageBubble, ThemeAwareBackground, TypingBubble

class ChatMessageArea(ThemeAwareBackground):
    """
    Standalone Component for displaying chat messages.
    Encapsulates: Scroll Area, Message Bubbles, Auto-scroll Logic.
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ChatMessageArea")
        self.typing_indicator = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for Bubbles
        self.container = ThemeAwareBackground()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(20, 20, 20, 20)
        self.container_layout.setSpacing(16) # Good spacing between messages
        self.container_layout.addStretch()
        
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)

    def resizeEvent(self, event) -> None:
        """Ensure scroll stays at bottom if it was there before resize"""
        vsb = self.scroll_area.verticalScrollBar()
        # Detect if we are currently at the bottom (with a small margin)
        at_bottom = vsb.value() >= vsb.maximum() - 20
        
        super().resizeEvent(event)
        
        if at_bottom:
            # Use small delay to allow QScrollArea to update its maximum
            QTimer.singleShot(10, self.scroll_to_bottom)

    def add_user_message(self, text: str, image_paths: Optional[list[str]] = None) -> None:
        """Add a User message bubble (Right aligned)"""
        self._add_bubble(text, is_user=True, image_paths=image_paths)

    def add_ai_message(self, text: str, image_paths: Optional[list[str]] = None) -> None:
        """Add an AI message bubble (Left aligned)"""
        self._add_bubble(text, is_user=False, image_paths=image_paths)
        
    def _add_bubble(self, text: str, is_user: bool, image_paths: Optional[list[str]] = None) -> None:
        bubble = MessageBubble(text, is_user, image_paths)
        # Add before the stretch (which is the last item)
        count = self.container_layout.count()
        if count > 0:
            self.container_layout.insertWidget(count - 1, bubble)
        else:
            self.container_layout.addWidget(bubble)
            
        QTimer.singleShot(50, self.scroll_to_bottom)

    def clear(self) -> None:
        """Clear all messages"""
        while self.container_layout.count() > 1: # Keep the stretch
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Or just remove stretch and re-add? 
        # Actually safer to iterate cleanly:
        # Re-adding stretch ensures it's at the bottom
        pass # Improvement: Just clear everything and re-add stretch
        
        while self.container_layout.count():
             item = self.container_layout.takeAt(0)
             if item.widget():
                 item.widget().deleteLater()
        self.container_layout.addStretch()

    def show_typing_indicator(self, show: bool) -> None:
        """Show/Hide AI thinking indicator"""
        if show:
            if self.typing_indicator:
                return
            self.typing_indicator = TypingBubble()
            count = self.container_layout.count()
            if count > 0:
                self.container_layout.insertWidget(count - 1, self.typing_indicator)
            else:
                self.container_layout.addWidget(self.typing_indicator)
            QTimer.singleShot(50, self.scroll_to_bottom)
        else:
            if self.typing_indicator:
                self.typing_indicator.deleteLater()
                self.typing_indicator = None

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the chat"""
        vsb = self.scroll_area.verticalScrollBar()
        vsb.setValue(vsb.maximum())
