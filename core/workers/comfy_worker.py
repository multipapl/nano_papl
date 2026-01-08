from PySide6.QtCore import QThread, Signal
from core.services.comfy_orchestrator import ComfyOrchestrator

class ComfyWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(float)
    finished_signal = Signal()
    error_signal = Signal(str)
    preview_signal = Signal(str, str, str) # input_path, output_path, prompt_text
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.manager = None

    def run(self):
        try:
            self.manager = ComfyOrchestrator(
                self.settings,
                log_callback=self.log_signal.emit,
                progress_callback=self.progress_signal.emit,
                preview_callback=self.preview_signal.emit
            )
            self.manager.process_batch()
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()

    def stop(self):
        if self.manager:
            self.manager.stop()
        self.quit()
