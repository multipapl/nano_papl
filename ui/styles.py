
class Colors:
    """Centralized Palette"""
    PRIMARY   = "#2da44e"  # GitHub Green (Success/Start)
    DANGER    = "#d32f2f"  # Material Red (Stop/Destructive)
    ACCENT    = "#0078d4"  # VS Code Blue (Focus/Active)
    BG_DARK   = "#252526"  # Input Background
    BG_DARKER = "#1E1E1E"  # Console/Terminal Background
    TEXT      = "#E0E0E0"  # Primary Text
    TEXT_DIM  = "#AAAAAA"  # Secondary Text
    TEXT_MUTED = "#888888" # Disabled/Placeholder Text
    BORDER    = "#3E3E42"  # Standard Border

class Styles:
    """Shared CSS Strings"""
    
    # Generic Widget Reset
    GLOBAL = f"""
        QWidget {{
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            color: {Colors.TEXT};
        }}
    """
    
    # Section Headers
    SECTION_HEADER = f"""
        QLabel {{
            font-size: 14px;
            font-weight: bold;
            color: #FFFFFF;
            padding-bottom: 5px;
            border-bottom: 1px solid #333333;
            margin-top: 10px;
        }}
    """
    
    # Inputs (Text, Spin, Combo)
    INPUT_FIELD = f"""
        QLineEdit, QSpinBox, QComboBox {{
            background-color: {Colors.BG_DARK};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
            padding: 6px;
            color: #F0F0F0;
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 1px solid {Colors.ACCENT};
            background-color: {Colors.BG_DARKER};
        }}
        QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{
            border: 1px solid #555555;
        }}
    """
    
    # Text Area (Logs / Console)
    TEXT_AREA_CONSOLE = f"""
        QTextEdit {{
            font-family: Consolas, monospace; 
            font-size: 11px; 
            color: #d4d4d4; 
            border: 1px solid {Colors.BORDER}; 
            background-color: {Colors.BG_DARKER};
        }}
    """

    # --- BUTTONS ---
    
    # Base Button
    BTN_BASE = f"""
        QPushButton {{
            background-color: #3E3E42;
            border: 1px solid #3E3E42;
            color: {Colors.TEXT};
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #505055;
            border: 1px solid #555555;
        }}
    """

    # Primary Action (Start) - GREEN
    BTN_PRIMARY = f"""
        QPushButton {{
            background-color: {Colors.PRIMARY};
            border: 1px solid {Colors.PRIMARY};
            color: white; 
            font-weight: bold; 
            font-size: 12px;
            border-radius: 4px;
            padding: 8px;
        }}
        QPushButton:hover {{ background-color: #2c974b; }}
        QPushButton:disabled {{ background-color: #444; color: #888; }}
    """

    # Destructive Action (Stop) - RED
    BTN_DANGER = f"""
        QPushButton {{
            background-color: {Colors.DANGER};
            border: 1px solid {Colors.DANGER};
            color: white; 
            font-weight: bold; 
            font-size: 12px;
            border-radius: 4px;
            padding: 8px;
        }}
        QPushButton:hover {{ background-color: #c62828; }}
        QPushButton:disabled {{ background-color: #444; color: #888; }}
    """

    # Auxiliary / Info Action - BLUE
    BTN_ACCENT = f"""
        QPushButton {{
            background-color: {Colors.ACCENT};
            color: white;
            font-weight: bold;
            border-radius: 4px;
            padding: 8px;
        }}
        QPushButton:hover {{ background-color: #106ebe; }}
    """
    
    # Secondary (Ghost) - Transparent
    BTN_GHOST = f"""
        QPushButton {{
            background-color: transparent;
            border: 1px solid {Colors.BORDER};
            color: #CCCCCC;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background-color: #2D2D30;
            border: 1px solid #555555;
            color: #FFFFFF;
        }}
    """
