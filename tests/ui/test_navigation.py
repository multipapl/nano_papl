import pytest
from ui.pages.batch_page import BatchPage
from ui.pages.constructor_page import ConstructorPage
from ui.pages.settings_page import SettingsInterface
from ui.pages.tools_page import ToolsPage

def test_pages_instantiation(qtbot):
    """Перевірка, що всі основні сторінки можуть бути створені без помилок."""
    
    # 1. Settings
    settings = SettingsInterface()
    qtbot.addWidget(settings)
    assert settings is not None
    
    # 2. Tools
    tools = ToolsPage()
    qtbot.addWidget(tools)
    assert tools is not None
    
    # 3. Batch
    batch = BatchPage()
    qtbot.addWidget(batch)
    assert batch is not None
    
    # 4. Constructor
    constructor = ConstructorPage()
    qtbot.addWidget(constructor)
    assert constructor is not None
