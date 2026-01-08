from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer
from core.utils import config_helper
from typing import Dict, Any
import logging


class BaseTab(QWidget):
    """
    Base class for all tabs with automated state management.
    
    Provides:
    - Field registry for mapping config keys to widgets
    - Automated save_state() and load_state() methods
    - Optional auto-save functionality with debouncing
    
    Usage:
        class MyTab(BaseTab):
            def __init__(self):
                super().__init__()
                self._setup_ui()
                self._register_fields()
                self.load_state()
            
            def _register_fields(self):
                self.register_field("my_setting_key", self.my_widget)
    """
    
    def __init__(self):
        super().__init__()
        self.field_registry: Dict[str, Any] = {}
        self._autosave_timer = None
        self._autosave_enabled = False
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_field(self, config_key: str, widget: Any):
        """
        Register a widget for automated state management.
        
        Args:
            config_key: The key used to store this field in config.json
            widget: The widget instance (must implement get_state/set_state)
        """
        if not hasattr(widget, 'get_state') or not hasattr(widget, 'set_state'):
            self.logger.warning(
                f"Widget registered for '{config_key}' does not implement "
                f"get_state/set_state (type: {type(widget).__name__}). "
                f"Falling back to basic text/value extraction."
            )
        
        self.field_registry[config_key] = widget
        
        # Auto-connect to modified signal if available
        if self._autosave_enabled and hasattr(widget, 'modified'):
            widget.modified.connect(self._queue_autosave)
    
    def save_state(self):
        """
        Automatically saves state from all registered fields to config.
        Override this method if you need custom save logic.
        """
        config = config_helper.load_config()
        
        for key, widget in self.field_registry.items():
            try:
                if hasattr(widget, 'get_state'):
                    config[key] = widget.get_state()
                elif hasattr(widget, 'text'):
                    config[key] = widget.text()
                elif hasattr(widget, 'currentText'):
                    config[key] = widget.currentText()
                elif hasattr(widget, 'get_path'):
                    config[key] = widget.get_path()
                else:
                    self.logger.warning(f"Cannot extract state from widget for key '{key}'")
            except Exception as e:
                self.logger.error(f"Error saving state for '{key}': {e}")
        
        config_helper.save_config(config)
    
    def load_state(self):
        """
        Automatically loads state into all registered fields from config.
        Override this method if you need custom load logic.
        """
        config = config_helper.load_config()
        
        for key, widget in self.field_registry.items():
            if key not in config:
                continue
            
            try:
                value = config[key]
                if hasattr(widget, 'set_state'):
                    widget.set_state(value)
                elif hasattr(widget, 'setText'):
                    widget.setText(str(value))
                elif hasattr(widget, 'setCurrentText'):
                    widget.setCurrentText(str(value))
                elif hasattr(widget, 'set_path'):
                    widget.set_path(str(value))
                else:
                    self.logger.warning(f"Cannot restore state to widget for key '{key}'")
            except Exception as e:
                self.logger.error(f"Error loading state for '{key}': {e}")
    
    def enable_autosave(self, delay_ms: int = 1000):
        """
        Enable automatic state saving after a delay when any field changes.
        
        Args:
            delay_ms: Debounce delay in milliseconds (default 1000ms = 1 second)
        """
        self._autosave_enabled = True
        self._autosave_delay = delay_ms
        
        # Connect existing widgets
        for widget in self.field_registry.values():
            if hasattr(widget, 'modified'):
                widget.modified.connect(self._queue_autosave)
    
    def disable_autosave(self):
        """Disable automatic state saving"""
        self._autosave_enabled = False
        if self._autosave_timer:
            self._autosave_timer.stop()
    
    def _queue_autosave(self):
        """
        Queue an autosave operation with debouncing.
        Multiple triggers within the delay period will result in a single save.
        """
        if not self._autosave_enabled:
            return
        
        if self._autosave_timer is None:
            self._autosave_timer = QTimer()
            self._autosave_timer.setSingleShot(True)
            self._autosave_timer.timeout.connect(self._do_autosave)
        
        # Restart the timer (debouncing)
        self._autosave_timer.start(self._autosave_delay)
    
    def _do_autosave(self):
        """Perform the actual save operation"""
        try:
            self.save_state()
            self.logger.debug("Auto-save completed")
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
