import pytest
from PySide6.QtCore import Qt, QMimeData, QUrl, QPoint, QPointF, QEvent
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from ui.widgets.drag_drop_overlay import DragDropOverlay
from PySide6.QtWidgets import QWidget

class MockDragEvent:
    def __init__(self, mime_data):
        self._mime_data = mime_data
    def mimeData(self):
        return self._mime_data
    def acceptProposedAction(self):
        pass
    def pos(self):
        return QPoint(0, 0)
    def position(self):
        # PySide6 uses position()
        from PySide6.QtCore import QPointF
        return QPointF(0, 0)
    def type(self):
        from PySide6.QtCore import QEvent
        return QEvent.Type.DragEnter

def test_drag_drop_overlay_visibility(qtbot):
    """Перевірка появи оверлею при перетягуванні файлів."""
    parent = QWidget()
    overlay = DragDropOverlay(parent)
    qtbot.addWidget(parent)
    
    assert overlay.isHidden()
    
    # Симулюємо DragEnter через eventFilter
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile("test.png")])
    
    event = QDragEnterEvent(QPoint(0, 0), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    
    overlay.eventFilter(parent, event)
    
    assert not overlay.isHidden()
    assert overlay._drag_active is True
