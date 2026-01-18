from core.workers.base_worker import BaseWorker
from core.services.comfy_orchestrator import ComfyOrchestrator
from PySide6.QtCore import Signal

class ComfyWorker(BaseWorker):
    """
    Background worker for ComfyUI batch processing.
    Refactored to inherit from BaseWorker.
    """
    log_signal = Signal(str)
    # Inherits progress_signal = Signal(float)
    # Inherits finished_signal = Signal()
    # Inherits error_signal = Signal(str)
    preview_signal = Signal(str, str, str) # input_path, output_path, prompt_text
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.manager = None

    def execute(self):
        """
        Main logic for ComfyUI processing. Overrides BaseWorker.execute().
        """
        self.manager = ComfyOrchestrator(
            self.settings,
            log_callback=self.log_signal.emit,
            progress_callback=self.progress_signal.emit,
            preview_callback=self.preview_signal.emit
        )
        self.manager.process_batch()

    def stop(self):
        """Standard stop with additional orchestrator cleanup."""
        if self.manager:
            self.manager.stop()
        super().stop()
        self.quit()
