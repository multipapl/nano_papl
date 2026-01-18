import os
from pathlib import Path
from core import constants

class PathProvider:
    """
    Centralized provider for file system paths.
    Eliminates hardcoded paths scattered across the codebase.
    """
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PathProvider, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Determine the root of the application or the user's workspace
        # For now, we assume the current working directory or a specific env var
        self.app_root = Path(os.getcwd())
        
        self.documents_dir = Path(os.path.expanduser("~/Documents"))
        self.default_project_dir = self.documents_dir / constants.APP_NAME.replace(" ", "")
        
        # Ensure default directory exists
        self.default_project_dir.mkdir(parents=True, exist_ok=True)

    def get_app_root(self) -> Path:
        return self.app_root

    def get_default_projects_path(self) -> Path:
        return self.default_project_dir

    def get_renders_dir(self, project_path: Path) -> Path:
        """Returns the standard _renders directory for a given project path."""
        return project_path / constants.RENDERS_DIR_NAME

    def get_optimized_dir(self, project_path: Path) -> Path:
        """Returns the standard optimized images directory for a given project path."""
        return project_path / constants.OPTIMIZED_DIR_NAME

    def get_prompts_file(self, project_path: Path) -> Path:
        """Returns the path to the prompts.md file."""
        return project_path / constants.DEFAULT_PROMPTS_FILE

    def get_temp_dir(self) -> Path:
        temp_path = self.app_root / "temp"
        temp_path.mkdir(exist_ok=True)
        return temp_path

    def get_thumbnails_dir(self) -> Path:
        """Returns the centralized cache directory for chat thumbnails."""
        # Use APPDATA for persistence if documents_dir is too 'clean'? 
        # For now, let's keep it in the default_project_dir (NanoPapl root)
        path = self.default_project_dir / constants.THUMBNAILS_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path
