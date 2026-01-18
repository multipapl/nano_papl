"""
Tests for ConstructorPage.
Covers initialization, state persistence, and mode switching.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication


@pytest.fixture
def constructor_page(qtbot):
    """Create ConstructorPage with mocked dependencies."""
    from core.utils import config_helper
    from ui.pages.constructor_page import ConstructorPage
    
    # Force reload config manager with test isolation
    config_helper.config_manager.reload()
    
    page = ConstructorPage(config_manager=config_helper.config_manager)
    qtbot.addWidget(page)
    return page


class TestConstructorPageInitialization:
    """Tests for ConstructorPage initialization."""
    
    def test_constructor_page_creates_successfully(self, constructor_page):
        """Verify page initializes without errors."""
        assert constructor_page is not None
        assert constructor_page.objectName() == "ConstructorPage"
    
    def test_constructor_page_has_required_widgets(self, constructor_page):
        """Verify essential widgets are created."""
        # Preset toolbar
        assert hasattr(constructor_page, 'preset_bar')
        # Navigation (SegmentedWidget)
        assert hasattr(constructor_page, 'nav')
        # General widget
        assert hasattr(constructor_page, 'general_widget')
        # Seasons orchestrator
        assert hasattr(constructor_page, 'seasons_orchestrator')
        # Single prompt widget
        assert hasattr(constructor_page, 'single_widget')
    
    def test_constructor_page_has_generator(self, constructor_page):
        """Verify PromptGenerator is initialized."""
        assert hasattr(constructor_page, 'generator')
        assert constructor_page.generator is not None


class TestConstructorPageStatePersistence:
    """Tests for state save/load functionality."""
    
    def test_save_state_does_not_raise(self, constructor_page):
        """Verify save_state executes without errors."""
        # Should not raise
        constructor_page.save_state()
    
    def test_load_state_does_not_raise(self, constructor_page):
        """Verify load_state executes without errors."""
        # Should not raise (called during init, but test explicit call)
        constructor_page.load_state()


class TestConstructorPageModes:
    """Tests for mode switching (seasons vs single prompt)."""
    
    def test_stacked_widget_exists(self, constructor_page):
        """Verify stacked widget for mode switching exists."""
        assert hasattr(constructor_page, 'stacked_widget')
    
    def test_nav_widget_exists(self, constructor_page):
        """Verify navigation widget exists."""
        assert hasattr(constructor_page, 'nav')
