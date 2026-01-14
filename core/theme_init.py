from qfluentwidgets import setTheme, Theme, setThemeColor

def init_theme():
    """
    Initialize global application theme settings.
    
    - Forces Dark Theme.
    - Sets a professional 'Soft Blue' accent color (#4cc2ff) 
      to replace the default 'Toxic Cyan'.
    """
    setTheme(Theme.DARK)
    
    # Soft Blue / Sky Blue for a professional modern look
    # Replaces the default cyan/pro teal
    from core.utils import config_helper
    from qfluentwidgets import isDarkTheme
    
    if isDarkTheme():
        saved_color = config_helper.get_value("theme_color_dark", "#4cc2ff")
    else:
        saved_color = config_helper.get_value("theme_color_light", "#0078d4")
        
    setThemeColor(saved_color) 
