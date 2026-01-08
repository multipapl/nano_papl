from PySide6.QtWidgets import QLabel, QComboBox, QHBoxLayout, QWidget
from ui.widgets.stateful_widget import SettingRowWidget
from ui.widgets.path_selector import PathSelectorWidget
from ui.styles import Styles
from typing import List


class UIFactory:
    """
    Factory class for creating common UI patterns.
    Reduces boilerplate by standardizing widget creation.
    """
    
    @staticmethod
    def create_input_with_reset(
        default_value: str = "",
        reset_value: str = None,
        placeholder: str = ""
    ) -> SettingRowWidget:
        """
        Creates an input field with an integrated reset button.
        
        Args:
            default_value: Initial value for the input
            reset_value: Value to restore on reset (defaults to default_value)
            placeholder: Placeholder text for the input
        
        Returns:
            SettingRowWidget instance
        
        Example:
            widget = UIFactory.create_input_with_reset("Default", placeholder="Enter text...")
            layout.addRow("Label:", widget)
        """
        return SettingRowWidget(
            default_value=default_value,
            reset_value=reset_value,
            placeholder=placeholder
        )
    
    @staticmethod
    def create_combo_row(
        items: List[str],
        default_index: int = 0,
        label_text: str = None
    ) -> QWidget:
        """
        Creates a combo box, optionally with a label in a horizontal layout.
        
        Args:
            items: List of items for the combo box
            default_index: Index of the default selected item
            label_text: Optional label text (if None, only combo is returned)
        
        Returns:
            QWidget containing the combo (and label if specified)
        
        Example:
            widget = UIFactory.create_combo_row(["Option 1", "Option 2"], label_text="Select:")
            layout.addWidget(widget)
        """
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentIndex(default_index)
        combo.setStyleSheet(Styles.INPUT_FIELD)
        
        if label_text:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)
            
            label = QLabel(label_text)
            layout.addWidget(label)
            layout.addWidget(combo)
            
            return container
        
        return combo
    
    @staticmethod
    def create_path_selector(
        label_text: str,
        select_file: bool = False,
        default_path: str = "",
        dialog_title: str = "Select Path",
        show_label: bool = True
    ) -> PathSelectorWidget:
        """
        Creates a path selector widget with browse button and drag-drop support.
        
        Args:
            label_text: Label for the path selector
            select_file: If True, selector opens file dialog; if False, folder dialog
            default_path: Initial path value
            dialog_title: Title for the file/folder dialog
            show_label: Whether to show the label above the input
        
        Returns:
            PathSelectorWidget instance
        
        Example:
            widget = UIFactory.create_path_selector("Input Folder:", select_file=False)
            layout.addWidget(widget)
        """
        return PathSelectorWidget(
            label_text=label_text,
            default_path=default_path,
            select_file=select_file,
            dialog_title=dialog_title,
            show_label=show_label
        )
    
    @staticmethod
    def create_labeled_input(
        label_text: str,
        default_value: str = "",
        reset_value: str = None,
        placeholder: str = ""
    ) -> tuple[QLabel, SettingRowWidget]:
        """
        Creates a label and input widget pair (useful for QFormLayout).
        
        Args:
            label_text: Text for the label
            default_value: Initial value for the input
            reset_value: Value to restore on reset
            placeholder: Placeholder text
        
        Returns:
            Tuple of (QLabel, SettingRowWidget)
        
        Example:
            label, widget = UIFactory.create_labeled_input("Name:", default_value="John")
            form_layout.addRow(label, widget)
        """
        label = QLabel(label_text)
        widget = SettingRowWidget(
            default_value=default_value,
            reset_value=reset_value,
            placeholder=placeholder
        )
        return label, widget
