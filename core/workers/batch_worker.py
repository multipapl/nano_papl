from PySide6.QtCore import QThread, Signal
import datetime
from pathlib import Path

from core.services.generation_service import GenerationService
from core.utils.path_provider import PathProvider
from core.utils import prompt_parser, image_utils, naming
from core.utils.image_utils import SUPPORTED_IMAGE_FORMATS
from core.logger import logger

class BatchWorker(QThread):
    """
    Background worker for processing batch generation tasks.
    
    Responsibilities:
    - Iterating through project folders
    - Calculating total workload and ETA
    - Calling GenerationService for each item
    - Emitting progress, logs, and preview signals to UI
    """
    log_signal = Signal(str)
    progress_signal = Signal(float)
    finished_signal = Signal()
    error_signal = Signal(str)
    preview_signal = Signal(str, str, str) # input_path, output_path, prompt_text
    time_estimate_signal = Signal(str)
    api_call_signal = Signal()

    def __init__(self, api_key, input_path, output_path, resolution, ratio, output_format, model_id, check_logs, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.input_path = Path(input_path)
        # Use PathProvider for default output if not provided, but here we prioritize user arg
        self.output_path = Path(output_path) if output_path else PathProvider().get_renders_dir(self.input_path)
        
        self.resolution = resolution
        self.ratio = ratio
        self.output_format = output_format
        self.model_id = model_id
        self.check_logs = check_logs
        self.stop_requested = False
        
        # PathProvider for standardized filenames
        self.path_provider = PathProvider()

    def get_unified_filename(self, stem, title, ext):
        return naming.generate_filename(stem, title, ext)

    def run(self):
        self.log_signal.emit("--- INITIALIZING BATCH PROCESS ---")
        try:
            # Initialize Service
            gen_service = GenerationService(self.api_key, self.model_id)

            # --- Smart Folder Logic ---
            projects = []
            
            # Check 1: Is the input path itself a project?
            prompt_file = self.path_provider.get_prompts_file(self.input_path)
            if prompt_file.exists():
                self.log_signal.emit(f"Detected Single Project Mode: {self.input_path.name}")
                projects = [self.input_path]
            else:
                # Check 2: It's a root folder with subprojects
                projects = [d for d in self.input_path.iterdir() if d.is_dir()]
            
            if not projects:
                self.log_signal.emit("WARNING: No project folders found (checked for prompts.md).")
            
            valid_exts = SUPPORTED_IMAGE_FORMATS
            
            # --- Pre-calculation Phase ---
            self.log_signal.emit("Calculating workload...")
            total_operations = 0
            
            for project_dir in projects:
                if self.stop_requested: break
                
                # Logic must match the processing loop to be accurate
                # Logic must match the processing loop to be accurate
                image_source_dir = self.path_provider.get_optimized_dir(project_dir)
                if not image_source_dir.exists():
                    image_source_dir = project_dir
                
                prompt_path = self.path_provider.get_prompts_file(project_dir)
                prompts_data = self.parse_markdown_prompts(prompt_path)
                if not prompts_data: continue

                images = [f for f in image_source_dir.iterdir() if f.suffix.lower() in valid_exts]
                total_operations += len(images) * len(prompts_data)

            self.log_signal.emit(f"Total tasks found: {total_operations}")
            processed_count = 0
            start_time = None 

            if total_operations == 0:
                 self.log_signal.emit("Nothing to process.")
                 self.finished_signal.emit()
                 return # Exit early

            start_time = datetime.datetime.now()

            # --- Processing Phase ---
            for project_dir in projects:
                if self.stop_requested: break

                # Smart Image Source
                image_source_dir = self.path_provider.get_optimized_dir(project_dir)
                if not image_source_dir.exists():
                    image_source_dir = project_dir
                else:
                    self.log_signal.emit(f"  [INFO] Using optimized images from 'optimized' subfolder")

                prompt_path = self.path_provider.get_prompts_file(project_dir)
                prompts_data = self.parse_markdown_prompts(prompt_path)
                
                if not prompts_data:
                    self.log_signal.emit(f"Skipping '{project_dir.name}': Prompts file empty or missing valid prompt blocks.")
                    continue
                
                images = [f for f in image_source_dir.iterdir() if f.suffix.lower() in valid_exts]
                
                # Setup Output Directory (Always use original project name)
                # Ensure we respect the worker's output_path which might be a central _renders location
                # or a specific requested folder.
                # current logic: self.output_path / project_dir.name
                project_out = self.output_path / project_dir.name
                project_out.mkdir(parents=True, exist_ok=True)

                for img_path in images:
                    if self.stop_requested: break
                    
                    for data in prompts_data:
                        if self.stop_requested: break
                        self.log_signal.emit(f"  [{project_dir.name}] {img_path.name} -> {data['title']}")
                        
                        # Prepare Config for Service
                        config = {
                            'resolution': self.resolution,
                            'ratio': self.ratio,
                            'format': self.output_format,
                            'project_out_dir': project_out,
                            'save_log': self.check_logs,
                            'naming_func': self.get_unified_filename # Inject naming function
                        }

                        # Call Service
                        result = gen_service.generate_image(data, img_path, config)
                        
                        if result['success']:
                            if result.get('is_diff_resolution'):
                                self.log_signal.emit(f"    [WARN] Resolution Mismatch! (marked as _diff)")
                            
                            self.log_signal.emit(f"    [OK] Saved: {result['saved_path'].name}")
                            self.api_call_signal.emit()
                            self.preview_signal.emit(str(img_path), str(result['saved_path']), data['prompt'])
                        else:
                            self.log_signal.emit(f"    [ERROR] {result['error']}")
                            logger.error(f"DEBUG: Failed prompt:\n{data['prompt']}")

                        # --- Progress & ETA Update ---
                        processed_count += 1
                        
                        progress_val = (processed_count / total_operations) * 100
                        self.progress_signal.emit(progress_val)
                        
                        # ETA Calculation
                        if start_time:
                            elapsed = (datetime.datetime.now() - start_time).total_seconds()
                            if processed_count > 0:
                                avg_time_per_item = elapsed / processed_count
                                remaining_items = total_operations - processed_count
                                eta_seconds = int(avg_time_per_item * remaining_items)
                                
                                # Format ETA
                                if eta_seconds < 60:
                                    eta_str = f"{eta_seconds}s"
                                elif eta_seconds < 3600:
                                    m, s = divmod(eta_seconds, 60)
                                    eta_str = f"{m}m {s}s"
                                else:
                                    h, rem = divmod(eta_seconds, 3600)
                                    m, s = divmod(rem, 60)
                                    eta_str = f"{h}h {m}m"
                                
                                self.time_estimate_signal.emit(f"ETA: {eta_str}")

            if self.stop_requested:
                self.log_signal.emit("--- PROCESS STOPPED BY USER ---")
            else:
                self.log_signal.emit("--- BATCH PROCESS COMPLETED ---")
                self.progress_signal.emit(100)

        except Exception as e:
            self.error_signal.emit(str(e))
        
        self.finished_signal.emit()

    def request_stop(self):
        self.stop_requested = True

    def parse_markdown_prompts(self, file_path):
        return prompt_parser.parse_markdown_prompts(file_path)
