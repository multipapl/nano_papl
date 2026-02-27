import pytest
from ui.widgets.constructor.single_prompt import SinglePromptWidget
from core.generator import PromptGenerator

@pytest.fixture
def template_data():
    gen = PromptGenerator()
    return gen.get_template_data()

def test_single_prompt_generation(qtbot, template_data):
    """Verify that changing fields updates the prompt output."""
    widget = SinglePromptWidget(template_data)
    qtbot.addWidget(widget)
    
    # 1. Check default (Pre-filled from templates)
    default_text = widget.text_out.toPlainText()
    assert "viewport" in default_text
    assert "landscape" in default_text
    # Pre-filled override fields
    assert widget.entry_input.text() == template_data["input_types"]["Viewport"]
    
    # 2. Change location
    widget.entry_loc.setText("Modern Cabin")
    assert "Modern Cabin" in widget.text_out.toPlainText()
    
    # 3. Change selection (Updates LineEdit)
    widget.combo_input.setCurrentText("Render")
    assert widget.entry_input.text() == template_data["input_types"]["Render"]
    assert "Retouch" in widget.text_out.toPlainText()
    
    # 4. Christmas Mode (Uses dedicated Xmas description field)
    widget.chk_xmas.setChecked(True)
    custom_xmas = "Beautiful lights and trees."
    widget.entry_xmas.setText(custom_xmas)
    assert custom_xmas in widget.text_out.toPlainText()
    
    # 5. Manual Override in LineEdit
    widget.entry_input.setText("Custom Prompt Header")
    assert "Custom Prompt Header" in widget.text_out.toPlainText()
    assert "Retouch" not in widget.text_out.toPlainText()
