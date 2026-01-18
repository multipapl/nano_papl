"""
Resource Manager for Nano Papl.
Centralizes all asset paths and resource loading with fallback support.
"""
import sys
import os
from pathlib import Path
from typing import Optional
from PySide6.QtGui import QIcon
from core.logger import logger


class ResourceManager:
    """
    Singleton manager for application resources.
    Provides typed accessors for icons, data files, and paths.
    Handles PyInstaller bundling and missing resource fallbacks.
    """
    _instance = None
    
    # Default fallback paths
    ASSETS_DIR = "assets"
    DATA_DIR = "data"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance._base_path = cls._get_base_path()
            cls._instance._icon_cache = {}
        return cls._instance
    
    @staticmethod
    def _get_base_path() -> Path:
        """Get base path, handling PyInstaller bundling."""
        try:
            # PyInstaller creates temp folder with path in _MEIPASS
            return Path(sys._MEIPASS)
        except AttributeError:
            return Path(os.path.abspath("."))
    
    def get_path(self, relative_path: str) -> Path:
        """
        Get absolute path to a resource.
        
        Args:
            relative_path: Path relative to project root (e.g., "data/templates.json")
            
        Returns:
            Absolute Path object
        """
        return self._base_path / relative_path
    
    def get_data_file(self, filename: str) -> Path:
        """
        Get path to a data file.
        
        Args:
            filename: Name of file in data/ directory
            
        Returns:
            Path to the data file
        """
        return self._base_path / self.DATA_DIR / filename
    
    def get_asset(self, filename: str) -> Path:
        """
        Get path to an asset file.
        
        Args:
            filename: Name of file in assets/ directory
            
        Returns:
            Path to the asset file
        """
        return self._base_path / self.ASSETS_DIR / filename
    
    def icon(self, name: str, fallback: str = "ico.ico") -> QIcon:
        """
        Get a QIcon by name with caching and fallback support.
        
        Args:
            name: Icon name (without extension) or full filename
            fallback: Fallback icon if primary not found
            
        Returns:
            QIcon object
        """
        # Check cache
        if name in self._icon_cache:
            return self._icon_cache[name]
        
        # Try with common extensions
        icon_path = None
        for ext in ["", ".ico", ".png", ".svg"]:
            candidate = self._base_path / self.ASSETS_DIR / f"{name}{ext}"
            if candidate.exists():
                icon_path = candidate
                break
        
        # Fallback
        if not icon_path:
            fallback_path = self._base_path / self.ASSETS_DIR / fallback
            if fallback_path.exists():
                icon_path = fallback_path
                logger.warning(f"Icon '{name}' not found, using fallback: {fallback}")
            else:
                logger.error(f"Icon '{name}' and fallback '{fallback}' not found")
                return QIcon()
        
        icon = QIcon(str(icon_path))
        self._icon_cache[name] = icon
        return icon
    
    def exists(self, relative_path: str) -> bool:
        """Check if a resource exists."""
        return (self._base_path / relative_path).exists()
    
    @property
    def base_path(self) -> Path:
        """Get the application base path."""
        return self._base_path
    
    @property
    def assets_path(self) -> Path:
        """Get the assets directory path."""
        return self._base_path / self.ASSETS_DIR
    
    @property
    def data_path(self) -> Path:
        """Get the data directory path."""
        return self._base_path / self.DATA_DIR


# Singleton instance for convenience
Resources = ResourceManager()
