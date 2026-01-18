from PySide6.QtCore import QThread, Signal
from PIL import Image
from core.llm_client import LLMClient
from core.utils import config_helper, image_utils
from core.utils.path_provider import PathProvider
from core import constants
from pathlib import Path
import os
import datetime

class ChatWorker(QThread):
    response_signal = Signal(str, str) # Emits (text, image_path)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, api_key, model_id, history, user_message, image_paths=None, res="1K", ratio="1:1", session_id=None, image_format="PNG", parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.model_id = model_id
        self.session_id = session_id
        self.history = history 
        self.user_message = user_message
        self.image_paths = image_paths or []
        self.res = res
        self.ratio = ratio
        self.image_format = image_format
        
        # Load System Instruction from Config/Defaults
        config = config_helper.load_config()
        self.system_instruction = config.get("system_instruction", config_helper.DEFAULT_SYSTEM_INSTRUCTION)
        
    def run(self):
        try:
            # We assume "gemini" as default provider for now as per previous logic, 
            # but ideally this comes from config too.
            client = LLMClient("gemini", self.model_id, self.api_key)
            
            # Call Generic Generate with Native Params
            response_text, img_bytes = client.generate_chat(
                self.history, 
                self.user_message, 
                self.image_paths, 
                system_instruction=self.system_instruction,
                resolution=self.res,
                ratio=self.ratio
            )
            
            response_image_path = ""
            if img_bytes:
                # Save to [Data Root]/Generated_Images using PathProvider logic?
                # PathProvider has get_default_projects_path, get_documents_dir...
                # Current logic used config data_root or default.
                # Let's standardize on PathProvider if possible or respect config.
                
                # We can update PathProvider to read config if we want strict centralization,
                # but for this specific worker, let's keep it robust.
                
                config = config_helper.load_config()
                # Use PathProvider to get default if config missing
                pp = PathProvider()
                default_root = pp.get_default_projects_path() # ~/Documents/NanoPapl
                
                root_path = Path(config.get("data_root", str(default_root.parent))) # Wait, default_project_dir is .../NanoPapl
                # The previous code had `default_root = Path(...) / "NanoPapl"`.
                # If data_root in config is just `.../Documents`, we append NanoPapl?
                # Let's trust PathProvider.get_default_projects_path() is the main root for projects.
                # However, "Generated_Images" folder is usually at the root of the "App Data" folder (not APPDATA env, but user docs).
                
                # Let's use the PathProvider's app root concept or just use the Documents/NanoPapl root.
                save_root = Path(config.get("data_root", str(default_root)))
                
                out_dir = save_root / constants.GENERATED_IMAGES_DIR_NAME
                out_dir.mkdir(parents=True, exist_ok=True)
                
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                from io import BytesIO
                img = Image.open(BytesIO(img_bytes))
                
                ext = ".png" if self.image_format == "PNG" else ".jpg"
                save_path = out_dir / f"gen_{ts}{ext}"
                
                image_utils.save_image_with_format(img, save_path, self.image_format)
                
                response_image_path = str(save_path.absolute())

            self.response_signal.emit(str(response_text).strip(), response_image_path)
            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))
