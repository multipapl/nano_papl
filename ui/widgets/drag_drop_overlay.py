from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from ui.styles import Colors
import os


class DragDropOverlay(QWidget):
    """
    Reusable overlay widget that provides drag-and-drop functionality with visual feedback.
    
    Usage:
        overlay = DragDropOverlay(parent_widget)
        overlay.filesDropped.connect(some_handler)
    """
    filesDropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        # We don't need acceptDrops here because we rely on parent's events mostly,
        # but if we become visible and take over, we might need it.
        self.setAcceptDrops(True)
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True) # let clicks pass through when visible (if we want)
        # BUT we want to catch drops. 
        # Actually, let's keep it simple: 
        # 1. Hidden normally.
        # 2. Parent gets drag -> We show up (Transparent for mouse? No, we need to accept drop?)
        # Let's try: Parent handles EVERYTHING via event filter, we just Paint.
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True) # We are just visual
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
            if event.type() == event.Type.Resize:
                self.setGeometry(obj.rect())
            
            elif event.type() == event.Type.DragEnter:
                if event.mimeData().hasUrls():
                    self._drag_active = True
                    self.show()
                    self.raise_()
                    event.acceptProposedAction()
                    return True # Consume event
            
            elif event.type() == event.Type.DragMove:
                if self._drag_active:
                    event.acceptProposedAction()
                    return True
            
            elif event.type() == event.Type.DragLeave:
                self._drag_active = False
                self.hide()
                
            elif event.type() == event.Type.Drop:
                if self._drag_active:
                    # Handle Drop
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

    # We don't need dragEnterEvent/dropEvent on self if we are transparent for mouse
    # and catching parent events.

    def paintEvent(self, event):
        if not self._drag_active:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Semi-transparent background
        bg_color = QColor(Colors.ACCENT)
        bg_color.setAlpha(30)
        painter.fillRect(self.rect(), bg_color)
        
        # Dashed border
        pen = QPen(QColor(Colors.ACCENT), 3, Qt.DashLine)
        # Inset slightly
        r = self.rect().adjusted(2, 2, -2, -2)
        painter.setPen(pen)
        painter.drawRect(r)
        
        painter.end()
