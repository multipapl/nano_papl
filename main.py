
import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from ui.window import ModernWindow
from qfluentwidgets import setTheme, Theme

def qt_message_handler(mode, context, message):
    """
    Custom Qt message handler to suppress known QFluentWidgets warnings.
    
    QFont::setPointSize warnings come from QFluentWidgets internal components
    (NavigationBar, SettingCard, etc.) and cannot be fixed without modifying
    the library source code. These warnings don't affect functionality.
    """
    # Suppress QFont::setPointSize warnings from QFluentWidgets
    if "QFont::setPointSize: Point size <= 0" in message:
        return  # Silently ignore
    
    # Allow all other messages through
    if mode == QtMsgType.QtDebugMsg:
        print(f"Debug: {message}")
    elif mode == QtMsgType.QtWarningMsg:
        print(f"Warning: {message}")
    elif mode == QtMsgType.QtCriticalMsg:
        print(f"Critical: {message}")
    elif mode == QtMsgType.QtFatalMsg:
        print(f"Fatal: {message}")
        sys.exit(1)

def main():
    # Fix for taskbar icon on Windows
    if os.name == 'nt':
        myappid = 'nano_papl.v2.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # Install custom message handler BEFORE creating QApplication
    qInstallMessageHandler(qt_message_handler)
    
    # Enable High DPI scaling
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/ico.ico"))
    
    # Set default font (helps reduce some warnings)
    font = app.font()
    font.setPointSize(10) 
    app.setFont(font)

    # Set Theme (Dark by default) + Global Accent Color
    from core.theme_init import init_theme
    init_theme()
    
    window = ModernWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
