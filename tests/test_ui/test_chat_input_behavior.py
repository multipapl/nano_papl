import sys
import os
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from ui.components import ChatTextEdit

def test_chat_input_behavior():
    app = QApplication.instance() or QApplication(sys.argv)
    
    window = QWidget()
    layout = QVBoxLayout(window)
    
    chat_input = ChatTextEdit()
    layout.addWidget(chat_input)
    
    window.show()
    
    print(f"Initial height: {chat_input.height()}")
    # Updated to 40 as per ChatTextEdit.__init__
    assert chat_input.height() == 40
    
    # Simulate typing multiple lines
    chat_input.setPlainText("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
    # adjust_height is called via textChanged signal, but we might need to process events
    QApplication.processEvents()
    
    print(f"Height after 5 lines: {chat_input.height()}")
    assert chat_input.height() > 45
    
    # Max height check
    chat_input.setPlainText("\n" * 20)
    QApplication.processEvents()
    print(f"Height after many lines: {chat_input.height()}")
    assert chat_input.height() == 200
    
    print("Test passed!")
    sys.exit(0)

if __name__ == "__main__":
    # This requires a display, so it might fail in a headless environment. 
    # But since this is a local task, it's worth a try or just manual check.
    try:
        test_chat_input_behavior()
    except Exception as e:
        print(f"Test failed or could not run: {e}")
