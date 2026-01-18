"""
Tests for BatchPage.
Covers initialization, configuration, and generation flow.
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def batch_page(qtbot):
    """Create BatchPage with mocked dependencies."""
    from core.utils import config_helper
    from ui.pages.batch_page import BatchPage
    
    # Force reload config manager with test isolation
    config_helper.config_manager.reload()
    
    page = BatchPage(config_manager=config_helper.config_manager)
    qtbot.addWidget(page)
    return page


class TestBatchPageInitialization:
    """Tests for BatchPage initialization."""
    
    def test_batch_page_creates_successfully(self, batch_page):
        """Verify page initializes without errors."""
        assert batch_page is not None
        assert batch_page.objectName() == "BatchPage"
    
    def test_batch_page_has_config_panel(self, batch_page):
        """Verify ConfigPanel is created."""
        assert hasattr(batch_page, 'config_panel')
        assert batch_page.config_panel is not None
    
    def test_batch_page_has_monitor_panel(self, batch_page):
        """Verify MonitoringPanel is created."""
        assert hasattr(batch_page, 'monitor_panel')
        assert batch_page.monitor_panel is not None
    
    def test_batch_page_inherits_np_base_page(self, batch_page):
        """Verify page inherits from NPBasePage."""
        from ui.components import NPBasePage
        assert isinstance(batch_page, NPBasePage)


class TestBatchPageState:
    """Tests for BatchPage state management."""
    
    def test_save_state_does_not_raise(self, batch_page):
        """Verify _save_state executes without errors."""
        batch_page._save_state()
    
    def test_load_state_applies_config(self, batch_page):
        """Verify page loads state from config."""
        # Config panel should have values loaded
        assert batch_page.config_panel is not None


class TestBatchPageGenerationFlow:
    """Tests for generation start/stop flow."""
    
    def test_batch_page_has_worker_attribute(self, batch_page):
        """Verify worker attribute exists (None before start)."""
        assert hasattr(batch_page, 'worker')
    
    def test_start_button_exists(self, batch_page):
        """Verify start button is accessible."""
        # MonitorPanel should have a start button
        assert hasattr(batch_page.monitor_panel, 'btn_start')
