from PySide6.QtCore import QThread, Signal
import traceback

class BaseWorker(QThread):
    """
    Standard base class for all background tasks.
    Provides uniform signaling and error handling.
    """
    progress_signal = Signal(float)
    result_signal = Signal(object)
    error_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = True

    def stop(self):
        """Request the worker to stop gracefully."""
        self.is_running = False

    def run(self):
        """
        Internal QThread run method. 
        Calls the execute() method which must be overridden.
        """
        try:
            self.execute()
        except Exception as e:
            # Capture full traceback for easier debugging if needed, 
            # but emit a clean error message.
            error_detail = traceback.format_exc()
            print(f"Worker Error:\n{error_detail}")
            self.error_signal.emit(str(e))
        finally:
            self.is_running = False
            self.finished_signal.emit()

    def execute(self):
        """
        Main logic goes here. Subclasses must override this.
        Check self.is_running periodically for graceful stop.
        """
        raise NotImplementedError("Subclasses must implement execute()")
