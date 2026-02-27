import pytest
from ui.pages.batch_page import BatchPage
from ui.pages.constructor_page import ConstructorPage
from ui.pages.settings_page import SettingsInterface
from ui.pages.tools_page import ToolsPage

def test_pages_instantiation(qtbot):
    """Перевірка, що всі основні сторінки можуть бути створені без помилок."""
    from core.utils import config_helper
    cm = config_helper.config_manager
    
    # 1. Settings
    settings = SettingsInterface(cm)
    qtbot.addWidget(settings)
    assert settings is not None
    
    # 2. Tools
    tools = ToolsPage(None) # tools page parent is None by default in this test
    qtbot.addWidget(tools)
    assert tools is not None
    
    # 3. Batch
    batch = BatchPage(cm)
    qtbot.addWidget(batch)
    assert batch is not None
    
    # 4. Constructor
    constructor = ConstructorPage(cm)
    qtbot.addWidget(constructor)
    assert constructor is not None
