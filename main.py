import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PySide6.QtGui import QIcon, QPalette, QColor
from PySide6.QtCore import Qt

from ui.tab_constructor import TabConstructor
from ui.tab_batch import TabBatch
from ui.tab_chat import TabChat
from ui.tab_settings import TabSettings
from ui.tab_settings import TabSettings
# config_helper is imported inside tabs or main if needed for window geometry saving
from utils.resource_helper import get_resource_path

class NanoPaplApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Nano Papl | AI Archviz Automation")
        self.setWindowIcon(QIcon(get_resource_path("icon.png")))
        self.resize(1200, 900)

        # Central Widget & Tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Initialize Tabs
        self.tab_constructor = TabConstructor()
        self.tabs.addTab(self.tab_constructor, "Constructor")

        self.tab_batch = TabBatch()
        self.tabs.addTab(self.tab_batch, "Batch Studio")

        self.tab_chat = TabChat()
        self.tabs.addTab(self.tab_chat, "Ad-hoc Chat")
        self.tabs.addTab(TabSettings(), "Settings")

def set_dark_theme(app):
    app.setStyle("Fusion")
    palette = QPalette()
    # Deep Dark Backgrounds (Inspired by VS Code / Material Dark)
    palette.setColor(QPalette.Window, QColor(24, 24, 24))        # Main Window Background
    palette.setColor(QPalette.WindowText, QColor(240, 240, 240)) # Main Text
    palette.setColor(QPalette.Base, QColor(32, 32, 32))          # Input Fields / Lists
    palette.setColor(QPalette.AlternateBase, QColor(24, 24, 24))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, QColor(240, 240, 240))
    palette.setColor(QPalette.Button, QColor(45, 45, 45))        # Standard Buttons
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(64, 169, 255))        # Nice Blue Link
    palette.setColor(QPalette.Highlight, QColor(64, 169, 255))   # Selection Blue
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_dark_theme(app)
    
    window = NanoPaplApp()
    window.show()
    
    sys.exit(app.exec())
