"""Background worker for batch image resizing."""
from PySide6.QtCore import QThread, Signal

from core.services.image_resizer_service import ImageResizerService


class ResizerWorker(QThread):
    """
    Background thread for batch image resizing.
    
    Signals:
        progress: Emits (current, total) progress
        finished: Emits (success, message) when complete
        log_message: Emits log messages for UI display
    """
    
    progress = Signal(int, int)  # current, total
    finished = Signal(bool, str)  # success, message
    log_message = Signal(str)  # progress messages
    
    def __init__(
        self, 
        input_folder: str, 
        output_folder: str, 
        target_width: int, 
        target_height: int
    ):
        """
        Initialize resizer worker.
        
        Args:
            input_folder: Path to input folder
            output_folder: Path to output folder
            target_width: Target width in pixels
            target_height: Target height in pixels
        """
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.target_width = target_width
        self.target_height = target_height
        self._is_running = True
    
    def run(self):
        """Execute batch image resizing."""
        try:
            # Initialize service
            service = ImageResizerService(self.target_width, self.target_height)
            
            # Scan for images
            self.log_message.emit("🔍 Scanning for images...")
            image_pairs = service.scan_images(
                self.input_folder, 
                self.output_folder
            )
            total = len(image_pairs)
            
            if total == 0:
                self.finished.emit(False, "No images found to process")
                return
            
            self.log_message.emit(f"📊 Found {total} images to process")
            
            # Process images
            processed = 0
            failed = 0
            
            for i, (input_path, output_path) in enumerate(image_pairs):
                if not self._is_running:
                    self.finished.emit(False, "Processing cancelled")
                    return
                
                # Process image
                success = service.resize_image(input_path, output_path)
                
                if success:
                    processed += 1
                else:
                    failed += 1
                
                # Update progress
                self.progress.emit(i + 1, total)
            
            # Report results
            self.log_message.emit(f"✅ Processed: {processed} images")
            if failed > 0:
                self.log_message.emit(f"⚠️ Failed: {failed} images")
            
            message = f"Processing complete!\nProcessed: {processed}"
            if failed > 0:
                message += f"\nFailed: {failed}"
            
            self.finished.emit(True, message)
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")
    
    def stop(self):
        """Stop processing."""
        self._is_running = False
