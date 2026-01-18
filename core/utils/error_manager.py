"""
Global Error Manager for Nano Papl.
Centralizes error handling, logging, and user notification.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime
from core.logger import logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AppError:
    """Structured error representation."""
    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    context: Optional[str] = None  # e.g., "ChatWorker", "BatchPage"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Optional[str] = None  # Full traceback or extra info


class ErrorManager:
    """
    Singleton manager for application-wide error handling.
    Dispatches errors to appropriate handlers (logging, UI notifications).
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorManager, cls).__new__(cls)
            cls._instance._ui_handler = None
            cls._instance._error_history = []
        return cls._instance
    
    def set_ui_handler(self, handler: Callable[[AppError], None]):
        """
        Register a UI callback for displaying errors.
        Typically called by ModernWindow during initialization.
        """
        self._ui_handler = handler
    
    def report(
        self, 
        message: str, 
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[str] = None,
        details: Optional[str] = None,
        show_ui: bool = True
    ):
        """
        Report an error to the centralized system.
        
        Args:
            message: Human-readable error message
            severity: ErrorSeverity level
            context: Where the error occurred (e.g., "ChatWorker")
            details: Additional technical details (traceback)
            show_ui: Whether to display to user (False for silent logging)
        """
        error = AppError(
            message=message,
            severity=severity,
            context=context,
            details=details
        )
        
        # Always log
        self._log_error(error)
        
        # Store in history
        self._error_history.append(error)
        if len(self._error_history) > 100:
            self._error_history.pop(0)
        
        # UI notification (if handler registered and show_ui=True)
        if show_ui and self._ui_handler:
            self._ui_handler(error)
    
    def _log_error(self, error: AppError):
        """Write error to application log."""
        ctx = f"[{error.context}] " if error.context else ""
        log_msg = f"{ctx}{error.message}"
        
        if error.severity == ErrorSeverity.INFO:
            logger.info(log_msg)
        elif error.severity == ErrorSeverity.WARNING:
            logger.warning(log_msg)
        elif error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_msg)
            if error.details:
                logger.critical(f"Details: {error.details}")
        else:
            logger.error(log_msg)
            if error.details:
                logger.error(f"Details: {error.details}")
    
    def get_history(self, limit: int = 20):
        """Get recent error history."""
        return self._error_history[-limit:]
    
    def clear_history(self):
        """Clear error history."""
        self._error_history.clear()


# Singleton instance
error_manager = ErrorManager()
