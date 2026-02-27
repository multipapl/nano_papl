from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QPainter, QColor, QPen
from qfluentwidgets import themeColor
import os


class DragDropOverlay(QWidget):
    """
    Reusable overlay widget that provides drag-and-drop functionality with visual feedback.
    Updated to use qfluentwidgets theme system.
    """
    filesDropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        
        # We are visual only; clicks pass through, but we catch drops via parent event filter
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self._drag_active = False
        self.hide()
        
        if parent:
            parent.setAcceptDrops(True)
            parent.installEventFilter(self)
            self.setGeometry(parent.rect())

    def eventFilter(self, obj, event):
        if obj == self.parent():
            if event.type() == QEvent.Resize:
                self.setGeometry(obj.rect())
            
            elif event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    self._drag_active = True
                    self.show()
                    self.raise_()
                    event.acceptProposedAction()
                    return True
            
            elif event.type() == QEvent.DragMove:
                if self._drag_active:
                    event.acceptProposedAction()
                    return True
            
            elif event.type() == QEvent.DragLeave:
                self._drag_active = False
                self.hide()
                
            elif event.type() == QEvent.Drop:
                if self._drag_active:
                    paths = []
                    for url in event.mimeData().urls():
                        path = url.toLocalFile()
                        if os.path.isfile(path):
                            paths.append(path)
                    
                    if paths:
                        self.filesDropped.emit(paths)
                        event.acceptProposedAction()
                    
                    self._drag_active = False
                    self.hide()
                    return True
                    
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        if not self._drag_active:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Use qfluentwidgets theme color for accessibility and consistency
        accent = themeColor()
        
        # Semi-transparent background
        bg_color = QColor(accent)
        bg_color.setAlpha(30)
        painter.fillRect(self.rect(), bg_color)
        
        # Dashed border
        pen = QPen(accent, 3, Qt.DashLine)
        # Inset slightly
        r = self.rect().adjusted(4, 4, -4, -4)
        painter.setPen(pen)
        painter.drawRect(r)
        
        painter.end()
