from typing import Optional, List, Dict
from pathlib import Path
import os
import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt, QTimer
from qfluentwidgets import MessageBox, qconfig

# Modular Widgets
from ui.widgets.chat import ChatSidebar
from ui.widgets.chat.message_display import ChatMessageDisplay
from ui.widgets.chat.control_panel import ChatControlPanel
from ui.components import InputDialog, UIConfig, NPBasePage

# Managers & Core
from core.workers.chat_worker import ChatWorker
from core.history_manager import HistoryManager
from core.utils import config_helper
from core import constants
from core.models import GenerationConfig

class ChatInterface(NPBasePage):
    """
    Modern Chat Interface - Refactored for Modularity.
    Coordinates between HistoryManager, ChatWorker, and modular UI panels.
    """
    def __init__(
        self,
        history_manager: HistoryManager,
        config_manager,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ChatInterface")
        
        self.history_manager = history_manager
        self.config_manager = config_manager
        
        self.current_session = None
        self.current_session_id = None
        self.chat_history_api = []
        self.worker = None
        
        self._setup_ui()
        self._refresh_sidebar()
        
        # Auto-load latest session
        if self.chat_sidebar.count() > 0:
            self.chat_sidebar.select_first_item()
        
        # Robustness: ensure we always have a session even if auto-selection failed
        if self.current_session_id is None:
            self.start_new_chat()

    def _setup_ui(self):
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 1. SIDEBAR (History)
        self.chat_sidebar = ChatSidebar(self)
        self._connect_sidebar_signals()
        
        sidebar_visible = config_helper.get_value("chat_sidebar_visible", True)
        self.chat_sidebar.setVisible(sidebar_visible)
        self.splitter.addWidget(self.chat_sidebar)
        
        # 2. CHAT CONTENT AREA (Right panel)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Message Display (Header + Bubble Area)
        self.message_display = ChatMessageDisplay(self)
        self.message_display.toggleSidebarRequested.connect(self.toggle_sidebar)
        content_layout.addWidget(self.message_display, 1)
        
        # Control Panel (Tray + Input)
        self.control_panel = ChatControlPanel(self)
        self.control_panel.set_overlay_parent(self.message_display)
        self.control_panel.sendClicked.connect(self.on_send_clicked)
        self.control_panel.settingChanged.connect(self.save_current_settings)
        self.control_panel.clearClicked.connect(self.clear_current_chat)
        self.control_panel.folderClicked.connect(self.open_output_folder)
        content_layout.addWidget(self.control_panel)
        
        self.splitter.addWidget(self.content_widget)
        self.splitter.setStretchFactor(1, 1)
        self.main_layout.addWidget(self.splitter)
        
        self._apply_theme_style()
        qconfig.themeChanged.connect(self._apply_theme_style)

    def _connect_sidebar_signals(self):
        self.chat_sidebar.newChatClicked.connect(self.start_new_chat)
        self.chat_sidebar.newFolderClicked.connect(self.create_new_folder)
        self.chat_sidebar.sessionSelected.connect(self.on_session_selected_by_id)
        self.chat_sidebar.sessionDeleted.connect(self.delete_session)
        self.chat_sidebar.sessionRenamed.connect(self.rename_session)
        self.chat_sidebar.sessionMoved.connect(self.move_session_to_folder)
        self.chat_sidebar.folderDeleted.connect(self.delete_folder)

    # --- Session Management ---

    def _refresh_sidebar(self):
        sessions = self.history_manager.list_sessions()
        self.chat_sidebar.set_sessions(sessions)

    def start_new_chat(self, refresh_sidebar: bool = True):
        """Create a new chat session.
        
        Args:
            refresh_sidebar: If False, skip sidebar refresh (used when called as fallback after deletion)
        """
        self.current_session_id, self.current_session = self.history_manager.create_session()
        self.chat_history_api = []
        self.message_display.clear()
        self.message_display.add_ai_message("Hello! I am your AI assistant.")
        
        if refresh_sidebar:
            self._refresh_sidebar()
        
        if self.current_session:
            self.current_session["settings"] = self.control_panel.get_chat_config()
            self.history_manager.save_session(self.current_session_id, self.current_session)

    def on_session_selected_by_id(self, sid: str):
        if sid == self.current_session_id: return
        data = self.history_manager.load_session(sid)
        if data:
            self.current_session_id = sid
            self.current_session = data
            self._load_chat_from_data(data)

    def _load_chat_from_data(self, data):
        self.message_display.clear()
        self.chat_history_api = []
        
        for msg in data.get("messages", []):
            is_user = (msg["role"] == "user")
            text = msg.get("text", "")
            imgs = msg.get("images", [])
            
            if is_user: self.message_display.add_user_message(text, imgs)
            else: self.message_display.add_ai_message(text, imgs)
            
            self.chat_history_api.append({"role": msg["role"], "text": text})
            
        self.control_panel.set_chat_config(data.get("settings", {}))
        QTimer.singleShot(100, self.message_display.scroll_to_bottom)

    def handle_dropped_files(self, paths: List[str]):
        """Delegate attachment handling to control panel"""
        self.control_panel.handle_dropped_files(paths)

    # --- Core Logic ---

    def on_send_clicked(self, text: str, config: dict) -> None:
        if self.worker and self.worker.isRunning(): return
        imgs = self.control_panel.get_current_images()
        if not text and not imgs: return
        
        self.control_panel.set_enabled(False)
        self.message_display.add_user_message(text, imgs)
        self.message_display.show_typing_indicator(True)
        self.control_panel.clear_input()
        
        if self.current_session:
            self.current_session["messages"].append({
                "role": "user", "text": text, "images": list(imgs),
                "timestamp": datetime.datetime.now().isoformat()
            })
            self.history_manager.save_session(self.current_session_id, self.current_session)
        
        api_key = self.config_manager.config.api_key
        if not api_key:
            self.message_display.add_ai_message("❌ Error: API Key missing. Set in Settings.")
            self.control_panel.set_enabled(True)
            self.message_display.show_typing_indicator(False)
            return

        # Prepare Worker
        gen_config = GenerationConfig(
            model_id=config["model"],
            resolution=config["res"] if config["img_mode"] else "1K",
            aspect_ratio=config["ratio"] if config["img_mode"] else "1:1",
            image_format=config.get("format", "PNG"),
            img_mode=config["img_mode"]
        )
        
        self.worker = ChatWorker(
            api_key=api_key,
            config=gen_config,
            history=self.chat_history_api, 
            user_message=text,
            image_paths=imgs,
            session_id=self.current_session_id
        )
        self.worker.response_signal.connect(self.on_response)
        self.worker.error_signal.connect(self.on_error)
        
        self.showStateToolTip("Thinking", "Gemini is analyzing your request...")
        self.worker.start()

    def on_response(self, result) -> None:
        from core.models import GenerationResult
        
        # Unpack standardized result
        if isinstance(result, GenerationResult):
            text = result.text_response or ""
            image_path = result.output_path
            sid = result.session_id or self.current_session_id
        else:
            # Legacy fallback (tuple)
            text, image_path = result
            worker = self.sender()
            sid = getattr(worker, 'session_id', self.current_session_id)
        
        is_active = (sid == self.current_session_id)
        imgs = [image_path] if image_path else []
        
        if is_active:
            self.message_display.show_typing_indicator(False)
            self.finishStateToolTip("Ready", "Response received")
            
            # Get original user message from worker
            worker = self.sender()
            user_msg = getattr(worker, 'user_message', '')
            self.chat_history_api.append({"role": "user", "text": user_msg})
            self.chat_history_api.append({"role": "model", "text": text})
            self.message_display.add_ai_message(text, imgs)
            
            if self.current_session:
                self.current_session["messages"].append({
                    "role": "model", "text": text, "images": imgs,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                self.history_manager.save_session(sid, self.current_session)
            
            self.control_panel.set_enabled(True)
        else:
            # Background session update
            data = self.history_manager.load_session(sid)
            if data:
                data["messages"].append({
                    "role": "model", "text": text, "images": imgs,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                self.history_manager.save_session(sid, data)

    def on_error(self, error_msg: str):
        worker = self.sender()
        sid = getattr(worker, 'session_id', self.current_session_id)
        
        if sid == self.current_session_id:
            self.message_display.show_typing_indicator(False)
            self.message_display.add_ai_message(f"❌ Error: {error_msg}")
            self.finishStateToolTip("Error", "Generation failed")
            self.control_panel.set_enabled(True)

    # --- UI Actions ---

    def toggle_sidebar(self):
        visible = not self.chat_sidebar.isVisible()
        self.chat_sidebar.setVisible(visible)
        self.config_manager.config.chat_sidebar_visible = visible
        self.config_manager.save()

    def save_current_settings(self, config: dict):
        if self.current_session:
            self.current_session["settings"] = config
            self.history_manager.save_session(self.current_session_id, self.current_session)

    def clear_current_chat(self):
        if not self.current_session: return
        self.current_session["messages"] = []
        self.history_manager.save_session(self.current_session_id, self.current_session)
        self.message_display.clear()
        self.chat_history_api = []
        self.message_display.add_ai_message("Chat history cleared.")

    def open_output_folder(self):
        default_root = Path(os.path.expanduser("~")) / "Documents" / constants.APP_NAME.replace(" ", "")
        root_path = Path(self.config_manager.config.data_root or str(default_root))
        out_dir = root_path / constants.GENERATED_IMAGES_DIR_NAME
        out_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(out_dir)

    def _apply_theme_style(self):
        dark = qconfig.theme == Qt.Dark
        line_color = UIConfig.BORDER_SUBTLE_DARK if dark else UIConfig.BORDER_SUBTLE_LIGHT
        self.splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {line_color}; width: 1px; }}")
        self.control_panel.update_theme_style(dark)

    # --- History Operations (delegated to Sidebar) ---
    # These match the signals from sidebar to keep page logic here
    
    def delete_session(self, sid: str):
        """Delete a chat session and handle UI state properly."""
        was_current = (sid == self.current_session_id)
        
        # Delete the session file
        self.history_manager.delete_session(sid)
        
        # Clear state if we deleted the current session
        if was_current:
            self.current_session_id = None
            self.current_session = None
            self.chat_history_api = []
            self.message_display.clear()
        
        # Refresh sidebar to reflect deletion
        self._refresh_sidebar()
        
        # If we deleted current session, select another or create new
        if was_current:
            if self.chat_sidebar.count() > 0:
                self.chat_sidebar.select_first_item()
            else:
                # No sessions left - create new (skip refresh since we just did it)
                self.start_new_chat(refresh_sidebar=False)

    def rename_session(self, sid: str):
        data = self.history_manager.load_session(sid)
        if not data: return
        dialog = InputDialog("Rename Chat", "Enter a new title:", self)
        dialog.inputLineEdit.setText(data.get("title", ""))
        if dialog.exec():
            new_title = dialog.inputLineEdit.text().strip()
            if new_title:
                data["title"] = new_title
                self.history_manager.save_session(sid, data)
                self._refresh_sidebar()
                if sid == self.current_session_id: self.current_session["title"] = new_title

    def create_new_folder(self):
        dialog = InputDialog("New Folder", "Enter folder name:", self)
        if dialog.exec():
            name = dialog.inputLineEdit.text().strip()
            if name:
                self.history_manager.create_folder(name)
                self._refresh_sidebar()

    def move_session_to_folder(self, sid: str, folder: str):
        if self.history_manager.move_session(sid, folder):
            if sid == self.current_session_id: self.current_session["folder"] = folder
            self._refresh_sidebar()

    def delete_folder(self, folder_name: str):
        dialog = MessageBox("Delete Folder?", f"Permanently delete '{folder_name}' and all its chats?", self)
        dialog.yesButton.setText("Delete Everything")
        if dialog.exec():
            self.history_manager.delete_folder(folder_name)
            if self.current_session and self.current_session.get("folder") == folder_name:
                self.start_new_chat()
            self._refresh_sidebar()
