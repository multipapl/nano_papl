from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class GenerationConfig:
    """Configuration for AI generation (Chat or Batch)."""
    model_id: str
    resolution: str = "1K"
    aspect_ratio: str = "1:1"
    image_format: str = "PNG"
    img_mode: bool = True
    use_random_seed: bool = True
    seed_value: int = 0
    system_prompt: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "GenerationConfig":
        if not data:
            return cls(model_id="gemini-3-pro-image-preview") # Fallback to project default
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class ChatMessage:
    """A single message in a chat history."""
    role: str # 'user' or 'model'
    text: str
    images: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class ChatSession:
    """A complete chat session with history and settings."""
    id: str
    title: str
    folder: str = ""
    messages: List[ChatMessage] = field(default_factory=list)
    settings: Dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, sid: str, data: Dict) -> "ChatSession":
        messages = [
            ChatMessage(**msg) if isinstance(msg, dict) else msg 
            for msg in data.get("messages", [])
        ]
        return cls(
            id=sid,
            title=data.get("title", "New Chat"),
            folder=data.get("folder", ""),
            messages=messages,
            settings=data.get("settings", {})
        )

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "folder": self.folder,
            "messages": [asdict(m) for m in self.messages],
            "settings": self.settings
        }
@dataclass
class GenerationResult:
    """
    Standardized result from a generation worker.
    All workers emit this object through response_signal.
    """
    success: bool
    
    # Content (at least one should be populated on success)
    text_response: Optional[str] = None
    output_path: Optional[str] = None  # Path to generated image
    preview_image: Optional[str] = None  # Path or base64 for UI preview
    
    # Error handling
    error_message: Optional[str] = None
    
    # Context
    session_id: Optional[str] = None
    model_id: Optional[str] = None
    execution_time_ms: int = 0
    
    # Extensibility
    metadata: Dict = field(default_factory=dict)

    @classmethod
    def ok(cls, text: str = None, image_path: str = None, **kwargs) -> "GenerationResult":
        """Factory for successful result."""
        return cls(success=True, text_response=text, output_path=image_path, **kwargs)

    @classmethod
    def error(cls, message: str, **kwargs) -> "GenerationResult":
        """Factory for error result."""
        return cls(success=False, error_message=message, **kwargs)

@dataclass
class AppConfig:
    """Structure for application-wide configuration."""
    # Core API & Settings
    api_key: str = ""
    comfy_url: str = "http://127.0.0.1:8188"
    comfy_api_key: str = ""
    api_timeout: int = 600  # Default 600 seconds (10 mins)
    
    # UI & Appearance
    theme_color: str = "#0078d4"
    data_root: str = ""
    last_tab_index: int = 0
    chat_sidebar_visible: bool = True
    
    # Batch & Logging
    auto_save_logs: bool = False
    batch_save_logs: bool = True
    
    # Project & State (Constructor tab)
    constructor_project_name: str = "New Project"
    constructor_context: str = ""
    constructor_input_type: str = "Interior"
    constructor_scene_type: str = "Living Room"
    constructor_base_text: str = ""
    
    # Statistics & Misc
    api_usage: Dict = field(default_factory=dict)
    monthly_api_usage: Dict = field(default_factory=dict)
    
    # Internal: hold unknown keys to prevent data loss during migration
    _extra: Dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict) -> "AppConfig":
        known_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        extra_fields = {k: v for k, v in data.items() if k not in cls.__dataclass_fields__}
        return cls(**known_fields, _extra=extra_fields)

    def to_dict(self) -> Dict:
        data = asdict(self)
        extra = data.pop("_extra", {})
        return {**data, **extra}
