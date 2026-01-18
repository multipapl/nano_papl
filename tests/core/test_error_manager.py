"""
Tests for ErrorManager.
Covers singleton behavior, error reporting, and severity handling.
"""
import pytest
from core.utils.error_manager import ErrorManager, ErrorSeverity, AppError, error_manager


class TestErrorManagerSingleton:
    """Tests for singleton behavior."""
    
    def test_error_manager_is_singleton(self):
        """Verify single instance is returned."""
        em1 = ErrorManager()
        em2 = ErrorManager()
        assert em1 is em2
    
    def test_global_instance_exists(self):
        """Verify global error_manager instance is available."""
        assert error_manager is not None
        assert isinstance(error_manager, ErrorManager)


class TestErrorReporting:
    """Tests for error reporting functionality."""
    
    def test_report_stores_in_history(self):
        """Verify errors are stored in history."""
        error_manager.clear_history()
        
        error_manager.report("Test error", severity=ErrorSeverity.ERROR, show_ui=False)
        
        history = error_manager.get_history()
        assert len(history) == 1
        assert history[0].message == "Test error"
        assert history[0].severity == ErrorSeverity.ERROR
    
    def test_report_with_context(self):
        """Verify context is captured."""
        error_manager.clear_history()
        
        error_manager.report("Test", context="TestContext", show_ui=False)
        
        history = error_manager.get_history()
        assert history[0].context == "TestContext"
    
    def test_history_limit(self):
        """Verify history is limited to prevent memory issues."""
        error_manager.clear_history()
        
        # Add more than limit
        for i in range(150):
            error_manager.report(f"Error {i}", show_ui=False)
        
        history = error_manager.get_history()
        assert len(history) <= 100


class TestAppError:
    """Tests for AppError dataclass."""
    
    def test_app_error_creation(self):
        """Verify AppError fields are set correctly."""
        error = AppError(
            message="Test message",
            severity=ErrorSeverity.WARNING,
            context="TestModule"
        )
        
        assert error.message == "Test message"
        assert error.severity == ErrorSeverity.WARNING
        assert error.context == "TestModule"
        assert error.timestamp is not None
