from core.workers.base_worker import BaseWorker
from PIL import Image
from core.llm_client import LLMClient
from core.utils import config_helper, image_utils
from core.utils.path_provider import PathProvider
from core import constants
from core.models import GenerationConfig, GenerationResult
from pathlib import Path
import os
import datetime
import time
from io import BytesIO

class ChatWorker(BaseWorker):
    """
    ChatWorker migrated to BaseWorker.
    Handles background AI conversation and image generation.
    """
    # Keep response_signal for compatibility with ChatInterface for now
    response_signal = BaseWorker.result_signal 

    def __init__(self, api_key: str, config: GenerationConfig, history: list, user_message: str, image_paths=None, session_id=None, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.config = config
        self.history = history
        self.user_message = user_message
        self.image_paths = image_paths or []
        self.session_id = session_id
        
        # Load System Instruction
        app_config = config_helper.load_config()
        self.system_instruction = app_config.get("system_instruction", config_helper.DEFAULT_SYSTEM_INSTRUCTION)

    def execute(self):
        start_time = time.time()
        client = LLMClient("gemini", self.config.model_id, self.api_key)
        
        # Call LLM
        response_text, img_bytes = client.generate_chat(
            self.history, 
            self.user_message, 
            self.image_paths, 
            system_instruction=self.system_instruction,
            resolution=self.config.resolution,
            ratio=self.config.aspect_ratio
        )
        
        if not self.is_running:
            return

        response_image_path = ""
        if img_bytes:
            save_path = self._save_generated_image(img_bytes)
            response_image_path = str(save_path.absolute())

        execution_time = int((time.time() - start_time) * 1000)
        
        # Emit standardized GenerationResult
        result = GenerationResult.ok(
            text=str(response_text).strip(),
            image_path=response_image_path if response_image_path else None,
            session_id=self.session_id,
            model_id=self.config.model_id,
            execution_time_ms=execution_time
        )
        self.result_signal.emit(result)

    def _save_generated_image(self, img_bytes: bytes) -> Path:
        app_config = config_helper.load_config()
        pp = PathProvider()
        
        # Determine save directory
        default_root = pp.get_default_projects_path()
        save_root = Path(app_config.get("data_root", str(default_root)))
        out_dir = save_root / constants.GENERATED_IMAGES_DIR_NAME
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        img = Image.open(BytesIO(img_bytes))
        ext = ".png" if self.config.image_format == "PNG" else ".jpg"
        save_path = out_dir / f"gen_{ts}{ext}"
        
        image_utils.save_image_with_format(img, save_path, self.config.image_format)
        return save_path
