from typing import List, Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidgetItem
from PySide6.QtCore import Qt, Signal, QSize
from qfluentwidgets import TreeWidget, ToolButton, FluentIcon, BodyLabel, RoundMenu, Action, MenuAnimationType
from ui.components import NPButton, ThemeAwareBackground

class ChatTreeWidget(TreeWidget):
    """Subclass of TreeWidget to handle custom Drag & Drop logic for chat sessions."""
    
    sessionMoved = Signal(str, str) # Emits sid, folder_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(TreeWidget.InternalMove)
        self.setHeaderHidden(True)
        self.setIndentation(20)

    def dropEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        selected_item = self.currentItem()
        
        if not selected_item or selected_item.data(0, Qt.UserRole) != "session":
            super().dropEvent(event)
            return
            
        sid = selected_item.data(1, Qt.UserRole)
        target_folder = ""
        
        # Determine target folder based on where we dropped
        if item:
            if item.data(0, Qt.UserRole) == "folder":
                target_folder = item.data(1, Qt.UserRole)
            elif item.parent(): 
                target_folder = item.parent().data(1, Qt.UserRole)
        
        self.sessionMoved.emit(sid, target_folder)
        event.accept()

class ChatSidebar(ThemeAwareBackground):
    """
    Standalone Chat Sidebar Component.
    Encapsulates: History List, New Chat Button, Visual Styling.
    """
    
    # Signals
    newChatClicked = Signal()
    newFolderClicked = Signal()   # Emits to trigger folder name dialog
    sessionSelected = Signal(str) # Emits session ID
    sessionDeleted = Signal(str)  # Emits session ID
    sessionRenamed = Signal(str)  # Emits session ID to trigger rename dialog
    sessionMoved = Signal(str, str) # Emits session ID, target folder name
    folderDeleted = Signal(str)    # Emits folder name
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ChatSidebar")
        self.setMinimumWidth(0) # Allow collapsing to zero
        self.setMaximumWidth(300)
        
        self.folders = [] # Cached folder list for move menu
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header Buttons (New Chat + New Folder)
        header_layout = QHBoxLayout()
        self.btn_new = NPButton("New Chat", FluentIcon.ADD)
        self.btn_new.setToolTip("Start a fresh conversation")
        self.btn_new.clicked.connect(self.newChatClicked.emit)
        
        self.btn_new_folder = ToolButton(FluentIcon.FOLDER_ADD, self)
        self.btn_new_folder.setToolTip("Create new folder")
        self.btn_new_folder.setFixedSize(32, 32)
        self.btn_new_folder.clicked.connect(self.newFolderClicked.emit)
        
        header_layout.addWidget(self.btn_new, 1)
        header_layout.addWidget(self.btn_new_folder)
        layout.addLayout(header_layout)
        
        layout.addSpacing(10)
        
        # History Tree
        self.history_list = ChatTreeWidget(self)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._show_context_menu)
        self.history_list.itemClicked.connect(self._on_item_clicked)
        self.history_list.sessionMoved.connect(self.sessionMoved.emit)
        layout.addWidget(self.history_list)
        
    def set_sessions(self, structure: Dict) -> None:
        """Repopulate tree with folders and sessions"""
        self.history_list.clear()
        
        # Update folder cache
        folders = structure.get("folders", {})
        self.folders = list(folders.keys())
        
        # Add Folders
        folders = structure.get("folders", {})
        for folder_name, sessions in folders.items():
            folder_item = QTreeWidgetItem([folder_name])
            folder_item.setIcon(0, FluentIcon.FOLDER.icon())
            folder_item.setData(0, Qt.UserRole, "folder")
            folder_item.setData(1, Qt.UserRole, folder_name)
            self.history_list.addTopLevelItem(folder_item)
            
            for sess in sessions:
                self._add_session_item(sess, parent=folder_item)
                
        # Add Root Sessions
        root_sessions = structure.get("sessions", [])
        for sess in root_sessions:
            self._add_session_item(sess)

    def _add_session_item(self, sess: Dict, parent: Optional[QTreeWidgetItem] = None) -> None:
        """Helper to add session item to tree"""
        item = QTreeWidgetItem([sess["title"]])
        item.setData(0, Qt.UserRole, "session")
        item.setData(1, Qt.UserRole, sess["id"])
        
        if parent:
            parent.addChild(item)
        else:
            self.history_list.addTopLevelItem(item)

    def add_session(self, sess: Dict) -> None:
        """Add a single session (usually for new chats)"""
        # For simplicity, we refresh the whole tree or just add to top
        self._add_session_item(sess)

    def clear(self) -> None:
        """Clear all items"""
        self.history_list.clear()

    def _on_item_clicked(self, item: QTreeWidgetItem):
        type = item.data(0, Qt.UserRole)
        if type == "session":
            sid = item.data(1, Qt.UserRole)
            if sid:
                self.sessionSelected.emit(sid)

    def _show_context_menu(self, pos):
        """Show native Fluent context menu on right click"""
        item = self.history_list.itemAt(pos)
        if not item:
            return
            
        type = item.data(0, Qt.UserRole)
        menu = RoundMenu(parent=self)
        
        if type == "session":
            self._add_session_actions(menu, item)
        elif type == "folder":
            self._add_folder_actions(menu, item)
        
        if not menu.isEmpty():
            menu.exec(self.history_list.mapToGlobal(pos), aniType=MenuAnimationType.DROP_DOWN)

    def _add_session_actions(self, menu: RoundMenu, item: QTreeWidgetItem):
        """Add actions for a chat session item"""
        sid = item.data(1, Qt.UserRole)
        
        rename_action = Action(FluentIcon.EDIT, "Rename", self)
        rename_action.triggered.connect(lambda: self.sessionRenamed.emit(sid))
        menu.addAction(rename_action)
        
        # Move to folder submenu
        move_menu = RoundMenu("Move to Folder", self)
        move_menu.setIcon(FluentIcon.FOLDER)
        
        to_root = Action("Root", self)
        to_root.triggered.connect(lambda: self.sessionMoved.emit(sid, ""))
        move_menu.addAction(to_root)
        
        # Use cached folders
        for folder in self.folders:
            act = Action(folder, self)
            act.triggered.connect(lambda _, f=folder: self.sessionMoved.emit(sid, f))
            move_menu.addAction(act)
            
        menu.addMenu(move_menu)
        menu.addSeparator()
        
        delete_action = Action(FluentIcon.DELETE, "Delete", self)
        delete_action.triggered.connect(lambda: self.sessionDeleted.emit(sid))
        menu.addAction(delete_action)

    def _add_folder_actions(self, menu: RoundMenu, item: QTreeWidgetItem):
        """Add actions for a folder item"""
        folder_name = item.data(1, Qt.UserRole)
        
        delete_action = Action(FluentIcon.DELETE, "Delete Folder", self)
        delete_action.triggered.connect(lambda: self.folderDeleted.emit(folder_name))
        menu.addAction(delete_action)
            
    def select_first_item(self):
        """Programmatically select the first session item if exists"""
        if self.history_list.topLevelItemCount() > 0:
            item = self.history_list.topLevelItem(0)
            if item.data(0, Qt.UserRole) == "session":
                self.history_list.setCurrentItem(item)
                self._on_item_clicked(item)
            elif item.childCount() > 0:
                child = item.child(0)
                self.history_list.setCurrentItem(child)
                self._on_item_clicked(child)

    def count(self) -> int:
        return self.history_list.topLevelItemCount()
