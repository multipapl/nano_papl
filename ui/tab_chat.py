from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QScrollArea, QLabel, QFrame, QSizePolicy, QFileDialog, QApplication,
    QComboBox, QToolButton, QSplitter, QListWidget, QListWidgetItem, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QEvent
from PySide6.QtGui import QPixmap, QIcon, QColor, QPalette, QPainter, QPainterPath
from core.llm_client import LLMClient
from google.genai import types # Still needed for types used in history for now, or just types use
from utils import config_helper
from core.history_manager import HistoryManager
from pathlib import Path
import datetime
import os

# --- UI Components ---
class TypingBubble(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            TypingBubble {
                background-color: #383838;
                border-radius: 15px;
                border-bottom-left-radius: 2px;
            }
            QLabel { color: #aaa; font-style: italic; font-size: 12px; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        self.lbl = QLabel("Thinking...")
        layout.addWidget(self.lbl)

class MessageBubble(QFrame):
    def __init__(self, text, is_user=False, image_paths=None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.is_user = is_user
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Style
        if is_user:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #2b5c8a; /* Muted Blue */
                    border-radius: 15px;
                    border-bottom-right-radius: 2px;
                }
                QLabel { color: white; font-size: 13px; }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #383838; /* Dark Gray */
                    border-radius: 15px;
                    border-bottom-left-radius: 2px;
                }
                QLabel { color: #e0e0e0; font-size: 13px; }
            """)

        # Images if attached
        if image_paths:
            if isinstance(image_paths, str): image_paths = [image_paths]
            for path in image_paths:
                if not path: continue
                # We show local path if exists, otherwise text placeholder?
                # If path is 'generated', it might be full path.
                lbl_img = QLabel()
                pix = QPixmap(path)
                if not pix.isNull():
                    if pix.width() > 400:
                        pix = pix.scaledToWidth(400, Qt.SmoothTransformation)
                    lbl_img.setPixmap(pix)
                    layout.addWidget(lbl_img)
                else:
                    layout.addWidget(QLabel(f"[Image: {Path(path).name}]"))

        # Text
        if text:
            lbl_text = QLabel(text)
            lbl_text.setWordWrap(True)
            lbl_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(lbl_text)

# --- Worker Thread ---
class ChatWorker(QThread):
    response_signal = Signal(str, str) # Emits (text, image_path)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, api_key, model_id, history, user_message, image_paths=None, res="1K", ratio="1:1", parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.model_id = model_id
        # provider handled by LLMClient internally now
        self.history = history 
        self.user_message = user_message
        self.image_paths = image_paths or []
        self.res = res
        self.ratio = ratio
        
        self.system_instruction = (
            "You are a Senior Architectural Visualization Art Director. "
            "Critique images strictly on lighting, composition, materials, and photorealism. "
            "Be technical, concise, and constructive. "
            "If asked to generate an image, you CAN do it (if provided tool allows). "
            "ALWAYS respect the requested Aspect Ratio and Resolution style in the prompt."
        )

    def run(self):
        try:
            client = LLMClient("gemini", self.model_id, self.api_key)
            
            # Call Generic Generate with Native Params
            response_text, img_bytes = client.generate_chat(
                self.history, 
                self.user_message, 
                self.image_paths, 
                system_instruction=self.system_instruction,
                resolution=self.res,
                ratio=self.ratio
            )
            
            response_image_path = ""
            if img_bytes:
                # Save to [Data Root]/Generated_Images
                config = config_helper.load_config()
                default_root = Path(os.path.expanduser("~")) / "Documents" / "NanoPapl"
                root_path = Path(config.get("data_root", str(default_root)))
                
                out_dir = root_path / "Generated_Images"
                out_dir.mkdir(parents=True, exist_ok=True)
                
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = out_dir / f"gen_{ts}.png"
                save_path.write_bytes(img_bytes)
                response_image_path = str(save_path.absolute())

            self.response_signal.emit(str(response_text).strip(), response_image_path)
            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))

class TabChat(QWidget):
    def __init__(self):
        super().__init__()
        # self.MODEL_ID removed, reading from config dynamicly
        
        # Init History with Config Path
        
        # Init History with Config Path
        config = config_helper.load_config()
        default_root = Path(os.path.expanduser("~")) / "Documents" / "NanoPapl"
        root_path = Path(config.get("data_root", str(default_root)))
        hist_path = root_path / "History"
        
        self.history_manager = HistoryManager(base_dir=hist_path)
        self.current_session = None # Dictionary data
        self.current_session_id = None
        self.chat_history_api = [] # For API context

        self._setup_ui()
        self._load_sidebar()
        
        # Select last session if exists, else wait
        if self.list_history.count() > 0:
            last_item = self.list_history.item(0) # Top of list (newest)
            self.list_history.setCurrentItem(last_item)
            self.on_session_clicked(last_item)
        else:
            self.add_message("Click '+ New Chat' to start.", is_user=False)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        # --- LEFT SIDEBAR ---
        sidebar = QWidget()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color: #1e1e1e; border-right: 1px solid #333;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)

        # New Chat Button
        btn_new = QPushButton("+ New Chat")
        btn_new.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; color: white; border-radius: 4px; padding: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2c974b; }
        """)
        btn_new.clicked.connect(self.start_new_chat)
        sidebar_layout.addWidget(btn_new)
        
        sidebar_layout.addWidget(QLabel("History"))
        
        # Session List
        self.list_history = QListWidget()
        self.list_history.setStyleSheet("""
            QListWidget {
                background-color: transparent; border: none; color: #ccc; outline: none;
            }
            QListWidget::item {
                background-color: transparent; padding: 4px; /* Space for widget */
            }
            QListWidget::item:selected {
                background-color: #333; border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a; border-radius: 4px;
            }
        """)
        self.list_history.itemClicked.connect(self.on_session_clicked)
        # Context menu still useful for other things or backup
        self.list_history.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_history.customContextMenuRequested.connect(self.show_context_menu)
        sidebar_layout.addWidget(self.list_history)

        splitter.addWidget(sidebar)

        # --- RIGHT CHAT AREA ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background-color: #1a1a1a;") 
        
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch() 
        self.typing_row = None
        
        self.scroll_area.setWidget(self.chat_container)
        right_layout.addWidget(self.scroll_area)

        # Config Bar
        config_bar = QFrame()
        config_bar.setStyleSheet("background-color: #252525; border-top: 1px solid #333;")
        config_layout = QHBoxLayout(config_bar)
        config_layout.setContentsMargins(10, 5, 10, 5)

        self.btn_img_mode = QPushButton("🎨 Gen Image")
        self.btn_img_mode.setCheckable(True)
        self.btn_img_mode.setChecked(True)
        self.btn_img_mode.setStyleSheet("""
            QPushButton { background-color: #333; color: #888; border-radius: 4px; padding: 4px 8px; }
            QPushButton:checked { background-color: #2b5c8a; color: white; }
        """)
        self.btn_img_mode.toggled.connect(self.toggle_img_mode)
        config_layout.addWidget(self.btn_img_mode)

        line1 = QFrame()
        line1.setFrameShape(QFrame.VLine)
        line1.setStyleSheet("background-color: #444;")
        config_layout.addWidget(line1)

        # Model Selector
        config_layout.addWidget(QLabel("Model:"))
        self.combo_model = QComboBox()
        self.combo_model.addItems([
            "gemini-3-pro-image-preview",
            "gemini-3-flash-preview"
        ])
        self.combo_model.setFixedWidth(220)
        # Revert to simple style to ensure clickability on Windows
        self.combo_model.setStyleSheet("""
            QComboBox {
                background-color: #333; color: white; border: 1px solid #444; border-radius: 4px; padding: 4px;
            }
            QComboBox::drop-down { border: none; }
        """)
        config_layout.addWidget(self.combo_model)

        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet("background-color: #444;")
        config_layout.addWidget(line)

        config_layout.addWidget(QLabel("Ratio:"))
        self.combo_ratio = QComboBox()
        self.combo_ratio.addItems(["1:1 (Square)", "16:9 (Landscape)", "4:3 (Photo)", "9:16 (Story)", "3:4 (Portrait)"])
        self.combo_ratio.setFixedWidth(120)
        config_layout.addWidget(self.combo_ratio)

        config_layout.addWidget(QLabel("  Res:"))
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1K (Standard)", "2K (Detailed)", "4K (Ultra High)"])
        self.combo_res.setFixedWidth(120)
        config_layout.addWidget(self.combo_res)

        # Clear Chat Button
        btn_clear = QPushButton("🗑️")
        btn_clear.setFixedSize(30, 25)
        btn_clear.setToolTip("Clear History of this Chat")
        btn_clear.setStyleSheet("""
            QPushButton { background-color: #333; color: #888; border-radius: 4px; }
            QPushButton:hover { background-color: #d32f2f; color: white; }
        """)
        btn_clear.clicked.connect(self.clear_current_chat)
        config_layout.addWidget(btn_clear)

        config_layout.addStretch()

        btn_folder = QPushButton("📂 Output Folder")
        btn_folder.setStyleSheet("background-color: #333; color: white; border-radius: 4px; padding: 4px 8px;")
        btn_folder.clicked.connect(self.open_output_folder)
        config_layout.addWidget(btn_folder)

        right_layout.addWidget(config_bar)

        # Input Area
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #252525;")
        input_col = QVBoxLayout(input_container)
        input_col.setContentsMargins(0, 0, 0, 0)
        input_col.setSpacing(0)

        self.tray_frame = QFrame()
        self.tray_frame.setVisible(False)
        self.tray_frame.setStyleSheet("background-color: #2a2a2a; border-top: 1px solid #333;")
        self.tray_layout = QHBoxLayout(self.tray_frame)
        self.tray_layout.setContentsMargins(10, 5, 10, 5)
        self.tray_layout.setAlignment(Qt.AlignLeft)
        input_col.addWidget(self.tray_frame)

        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)

        self.btn_attach = QPushButton("📎")
        self.btn_attach.setFixedSize(40, 40)
        self.btn_attach.setStyleSheet("""
            QPushButton { 
                background-color: #333; color: white; border-radius: 20px; font-size: 16px;
            }
            QPushButton:hover { background-color: #444; }
        """)
        self.btn_attach.clicked.connect(self.attach_image)
        input_layout.addWidget(self.btn_attach)
        
        self.current_image_paths = [] 

        self.entry_msg = QTextEdit()
        self.entry_msg.setPlaceholderText("Ask the Archviz Director... (Shift+Enter for new line)")
        self.entry_msg.setFixedHeight(45)
        self.entry_msg.setStyleSheet("""
            QTextEdit {
                background-color: #181818; color: white; border: 1px solid #333; border-radius: 20px; padding: 10px;
            }
            QTextEdit:focus { border: 1px solid #555; }
            QTextEdit:disabled { color: #555; background-color: #111; }
        """)
        self.entry_msg.installEventFilter(self)
        self.entry_msg.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Remove scrollbar artifacts
        input_layout.addWidget(self.entry_msg)

        self.btn_send = QPushButton("➤")
        self.btn_send.setFixedSize(40, 40)
        self.btn_send.setStyleSheet("""
            QPushButton { 
                background-color: #2da44e; color: white; border-radius: 20px; font-size: 16px; padding-left: 3px;
            }
            QPushButton:hover { background-color: #2c974b; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.btn_send.clicked.connect(self.send_message)
        input_layout.addWidget(self.btn_send)

        input_col.addWidget(input_frame)
        right_layout.addWidget(input_container)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0) # Sidebar fixed
        splitter.setStretchFactor(1, 1) # Chat expands
        main_layout.addWidget(splitter)

    # --- Sidebar & History Logic ---
    def _load_sidebar(self):
        self.list_history.clear()
        sessions = self.history_manager.list_sessions()
        for sess in sessions:
            item = QListWidgetItem()
            self.list_history.addItem(item)
            
            # Create Custom Widget for Item
            item_widget = QWidget()
            layout_w = QHBoxLayout(item_widget)
            layout_w.setContentsMargins(5, 2, 5, 2)
            
            lbl_title = QLabel(sess["title"])
            lbl_title.setStyleSheet("color: #ddd; background: transparent;")
            layout_w.addWidget(lbl_title)
            layout_w.addStretch()
            
            btn_del = QPushButton("🗑️") # Minimal ICON
            btn_del.setFixedSize(24, 24)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setToolTip("Delete Chat")
            btn_del.setStyleSheet("""
                QPushButton { background: transparent; color: #666; border: none; }
                QPushButton:hover { color: #ff4444; background: #330000; border-radius: 4px; }
            """)
            # Use closure to capture session ID
            btn_del.clicked.connect(lambda _, sid=sess["id"]: self.delete_session_by_id(sid))
            
            layout_w.addWidget(btn_del)
            
            item.setSizeHint(item_widget.sizeHint())
            self.list_history.setItemWidget(item, item_widget)
            
            # Store ID in item for click handling logic
            item.setData(Qt.UserRole, sess["id"])

    def delete_session_by_id(self, sid):
        self.history_manager.delete_session(sid)
        
        # If deleting current, clear UI
        if sid == self.current_session_id:
            self._clear_chat_ui()
            self.current_session = None
            self.current_session_id = None
            self.add_message("Chat deleted.", is_user=False)
            
        self._load_sidebar()

    def start_new_chat(self):
        # Save current session one last time if needed (usually handled on message)
        
        # Create new
        self.current_session_id, self.current_session = self.history_manager.create_session()
        self.chat_history_api = [] # Reset Context
        
        # Clear UI
        self._clear_chat_ui()
        self.add_message("Hello! I am your AI Art Director", is_user=False)
        
        # Refresh sidebar to show "New Chat"
        self._load_sidebar()
        # Highlight new
        # (Finding item by ID and selecting it is a bit verbose, skipping for now)

    def on_session_clicked(self, item):
        session_id = item.data(Qt.UserRole)
        # Even if clicking same session, maybe we want to reload? 
        # But usually check if different.
        if session_id == self.current_session_id: return
        
        data = self.history_manager.load_session(session_id)
        if data:
            self.current_session_id = session_id
            self.current_session = data
            self.load_chat_ui_from_data(data)

    def clear_current_chat(self):
        if not self.current_session: return
        
        # Clear Data
        self.current_session["messages"] = []
        self.history_manager.save_session(self.current_session_id, self.current_session)
        
        # Clear UI
        self._clear_chat_ui()
        self.chat_history_api = []
        self.add_message("Chat history cleared.", is_user=False)
        
        # Refresh Sidebar (Titles usually depend on first msg, might revert to "New Chat" or keep old title)
        # self._load_sidebar() # Optional: keeping old title might be less confusing

    def _clear_chat_ui(self):
        # Remove all widgets from layout except the spacer
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.chat_layout.addStretch()

    def load_chat_ui_from_data(self, data):
        self._clear_chat_ui()
        self.chat_history_api = [] # Rebuild API history context
        
        messages = data.get("messages", [])
        for msg in messages:
            role = msg["role"]
            text = msg.get("text", "")
            imgs = msg.get("images", [])
            
            is_user = (role == "user")
            self.add_message(text, is_user=is_user, image_paths=imgs)
            
            # Rebuild API context (Simulate internal storage for now)
            # LLMClient handles this more gracefully usually, but for now we reconstruct:
            entry = {"role": role, "text": text}
            self.chat_history_api.append(entry)
            
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def save_current_message(self, role, text, images=[]):
        if not self.current_session: return
        
        msg_obj = {
            "role": role,
            "text": text,
            "images": images,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.current_session["messages"].append(msg_obj)
        self.history_manager.save_session(self.current_session_id, self.current_session)
        self._load_sidebar() # Update titles/order

    def show_context_menu(self, pos):
        item = self.list_history.itemAt(pos)
        menu = QMenu()
        
        if item:
            delete_action = menu.addAction("Delete Chat")
            menu.addSeparator()
            
        open_folder_action = menu.addAction("📂 Open History Folder")
        
        action = menu.exec(self.list_history.mapToGlobal(pos))
        
        if item and action == delete_action:
            sid = item.data(Qt.UserRole)
            self.history_manager.delete_session(sid)
            self._load_sidebar()
            if sid == self.current_session_id:
                self.start_new_chat()
                
        if action == open_folder_action:
            # Open history folder
            config = config_helper.load_config()
            default_root = Path(os.path.expanduser("~")) / "Documents" / "NanoPapl"
            root_path = Path(config.get("data_root", str(default_root)))
            hist_path = root_path / "History"
            hist_path.mkdir(parents=True, exist_ok=True)
            os.startfile(hist_path)

    # --- Standard Chat Logic --- (Similar to before but with Save hooks)
    def send_message(self):
        text = self.entry_msg.toPlainText().strip()
        imgs = self.current_image_paths
        
        if not text and not imgs: return
        
        # UI
        self.add_message(text, is_user=True, image_paths=imgs)
        self.entry_msg.clear()
        self.current_image_paths = []
        self.update_tray()
        
        # Save to History
        self.save_current_message("user", text, imgs)
        
        self.set_processing_state(True)
        self.show_typing_indicator(True)

        api_key = config_helper.get_value("api_key", "")
        # provider = config.get("provider", "Gemini") 

        if not api_key:
            self.add_message("Error: API Key missing. Please set in Settings.", is_user=False)
            self.set_processing_state(False)
            self.show_typing_indicator(False)
            return

        res_val = "1K"
        ratio_val = "1:1"
        if self.btn_img_mode.isChecked():
            res_val = self.combo_res.currentText().split(" ")[0] # Convert "1K (Standard)" -> "1K"
            ratio_val = self.combo_ratio.currentText().split(" ")[0] # Convert "16:9 (Landscape)" -> "16:9"

        self.worker = ChatWorker(
            api_key, self.combo_model.currentText(), self.chat_history_api, text, imgs, 
            res=res_val, ratio=ratio_val, parent=self
        )
        self.worker.response_signal.connect(self.on_response)
        self.worker.error_signal.connect(self.on_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def on_response(self, text, image_path):
        self.show_typing_indicator(False)
        self.set_processing_state(False)
        
        # API History Check
        try:
             # Basic dict history for LLMClient
             self.chat_history_api.append({"role": "user", "text": self.worker.user_message})
             if text:
                 self.chat_history_api.append({"role": "model", "text": text})
        except: pass

        self.add_message(text, is_user=False, image_paths=image_path)
        
        # Save to History
        imgs_saved = [image_path] if image_path else []
        self.save_current_message("model", text, imgs_saved)

    def open_output_folder(self):
        config = config_helper.load_config()
        default_root = Path(os.path.expanduser("~")) / "Documents" / "NanoPapl"
        root_path = Path(config.get("data_root", str(default_root)))
        
        out_dir = root_path / "Generated_Images"
        out_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(out_dir)

    # --- Helper methods ---
    
    def toggle_img_mode(self, checked):
        self.combo_ratio.setEnabled(checked)
        self.combo_res.setEnabled(checked)
        if not checked:
            self.combo_ratio.setStyleSheet("color: #555;")
            self.combo_res.setStyleSheet("color: #555;")
        else:
            self.combo_ratio.setStyleSheet("")
            self.combo_res.setStyleSheet("")

    def eventFilter(self, obj, event):
        if obj == self.entry_msg and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def attach_image(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if paths:
            self.current_image_paths.extend(paths)
            self.update_tray()

    def update_tray(self):
        while self.tray_layout.count():
            item = self.tray_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not self.current_image_paths:
            self.tray_frame.setVisible(False)
            self.btn_attach.setStyleSheet("background-color: #333; color: white; border-radius: 20px;")
            return

        self.tray_frame.setVisible(True)
        self.btn_attach.setStyleSheet("background-color: #4a90e2; color: white; border-radius: 20px;")

        for path in self.current_image_paths:
            lbl = QLabel()
            pix = QPixmap(path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl.setPixmap(pix)
            lbl.setStyleSheet("border: 1px solid #555; border-radius: 4px;")
            self.tray_layout.addWidget(lbl)
            
        btn_clear = QPushButton("❌")
        btn_clear.setFixedSize(20, 20)
        btn_clear.setStyleSheet("background-color: #d32f2f; color: white; border-radius: 10px; font-size: 10px;")
        btn_clear.clicked.connect(self.clear_attachments)
        self.tray_layout.addWidget(btn_clear)
        self.tray_layout.addStretch()

    def clear_attachments(self):
        self.current_image_paths = []
        self.update_tray()

    def set_processing_state(self, processing):
        self.entry_msg.setDisabled(processing)
        self.btn_send.setDisabled(processing)
        self.btn_attach.setDisabled(processing)
        if processing:
            self.btn_send.setText("...")
            self.entry_msg.setPlaceholderText("Generating...")
        else:
            self.btn_send.setText("➤")
            self.entry_msg.setPlaceholderText("Ask the Archviz Director... (Shift+Enter for new line)")
            self.entry_msg.setFocus()

    def show_typing_indicator(self, show):
        if show:
            if self.typing_row: return
            self.typing_row = QWidget()
            layout = QHBoxLayout(self.typing_row)
            layout.setContentsMargins(10, 5, 10, 5)
            bubble = TypingBubble()
            layout.addWidget(bubble, 0, Qt.AlignLeft)
            layout.addStretch()
            self.chat_layout.addWidget(self.typing_row)
            QApplication.processEvents()
            self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())
        else:
            if self.typing_row:
                self.typing_row.deleteLater()
                self.typing_row = None

    def on_error(self, err):
        self.show_typing_indicator(False)
        self.set_processing_state(False)
        self.add_message(f"Error details: {err}", is_user=False)

    def add_message(self, text, is_user=False, image_paths=None):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 5, 10, 5)
        
        bubble = MessageBubble(text, is_user, image_paths)
        
        if is_user:
            row_layout.addStretch()
            row_layout.addWidget(bubble, 0, Qt.AlignRight)
        else:
            row_layout.addWidget(bubble, 0, Qt.AlignLeft)
            row_layout.addStretch()
            
        self.chat_layout.addWidget(row)
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())
