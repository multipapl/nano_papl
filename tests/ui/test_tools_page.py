"""
Tests for ToolsPage.
Covers initialization and sub-widget presence.
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def tools_page(qtbot):
    """Create ToolsPage instance."""
    from ui.pages.tools_page import ToolsPage
    
    page = ToolsPage()
    qtbot.addWidget(page)
    return page


class TestToolsPageInitialization:
    """Tests for ToolsPage initialization."""
    
    def test_tools_page_creates_successfully(self, tools_page):
        """Verify page initializes without errors."""
        assert tools_page is not None
        assert tools_page.objectName() == "ToolsPage"
    
    def test_tools_page_has_validator_widget(self, tools_page):
        """Verify ValidatorWidget is created."""
        assert hasattr(tools_page, 'validator')
        assert tools_page.validator is not None
    
    def test_tools_page_has_resizer_widget(self, tools_page):
        """Verify ResizerWidget is created."""
        assert hasattr(tools_page, 'resizer')
        assert tools_page.resizer is not None
    
    def test_tools_page_inherits_np_base_page(self, tools_page):
        """Verify page inherits from NPBasePage."""
        from ui.components import NPBasePage
        assert isinstance(tools_page, NPBasePage)
