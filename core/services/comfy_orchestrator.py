import json
import time
from pathlib import Path

from core.comfy_api import ComfyAPI
from core.constants import DEFAULT_NODE_MAPPING
from core.utils.path_provider import PathProvider
from core.utils import prompt_parser, image_utils, naming

class ComfyOrchestrator:
    """
    Orchestrates the batch processing of images through ComfyUI.
    Handles project scanning, task creation, and execution flow.
    """
    def __init__(self, settings, log_callback=None, progress_callback=None, preview_callback=None, node_mapping=None):
        self.settings = settings
        self.log_callback = log_callback or (lambda x: None)
        self.progress_callback = progress_callback or (lambda x: None)
        self.preview_callback = preview_callback or (lambda x, y, z: None) # input, output, prompt
        
        self.api = ComfyAPI(base_url=settings.get("comfy_url", "http://127.0.0.1:8188"))
        self.is_running = True
        self.project_provider = PathProvider() 
        
        # Dynamic Node Mapping
        self.node_mapping = node_mapping or DEFAULT_NODE_MAPPING

    def log(self, message):
        self.log_callback(message)

    def stop(self):
        self.is_running = False

    def process_batch(self) -> None:
        """
        Main entry point for processing the batch.
        Iterates through projects, creates tasks, and executes them.
        """
        # Input path from settings (UI) or PathProvider?
        input_path_str = self.settings.get("input_path", "")
        output_path_str = self.settings.get("output_path", "")
        
        input_path = Path(input_path_str) if input_path_str else self.project_provider.get_default_projects_path()
        output_path = Path(output_path_str) if output_path_str else self.project_provider.get_renders_dir(input_path)
        
        workflow_path = self.settings.get("workflow_path", "")
        
        self.log(f"--- Starting ComfyUI Batch ---")
        self.log(f"Mode: LIVE GENERATION")

        # 1. Load Workflow Template
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_template = json.load(f)
        except Exception as e:
            self.log(f"Error: Failed to load workflow template: {e}")
            return

        # 2. Project Detection
        projects = []
        prompt_file = self.project_provider.get_prompts_file(input_path) 
        
        if prompt_file.exists():
            self.log(f"Detected Single Project Mode: {input_path.name}")
            projects = [input_path]
        else:
            projects = [d for d in input_path.iterdir() if d.is_dir()]

        if not projects:
            self.log(f"Error: No project folders found in {input_path} (checked for prompts.md).")
            return

        # Use standard supported formats, convert set to tuple for suffix checking
        valid_exts = tuple(image_utils.SUPPORTED_IMAGE_FORMATS)

        # 3. Workload Calculation
        task_list = [] # List of (project_dir, img_path, prompt_data)

        for project_dir in projects:
            if not self.is_running: break
            
            # Use PathProvider for optimized Check
            image_source_dir = self.project_provider.get_optimized_dir(project_dir)
            if not image_source_dir.exists():
                image_source_dir = project_dir

            prompt_path = self.project_provider.get_prompts_file(project_dir)
            prompts_data = prompt_parser.parse_markdown_prompts(prompt_path)
            
            if not prompts_data:
                self.log(f"Skipping '{project_dir.name}': No valid prompts found.")
                continue

            images = [f for f in image_source_dir.iterdir() if f.suffix.lower() in valid_exts]
            
            if not images:
                self.log(f"Skipping '{project_dir.name}': No images found.")
                continue

            for img_path in images:
                for p_data in prompts_data:
                    task_list.append({
                        "project": project_dir,
                        "image": img_path,
                        "prompt": p_data
                    })

        total_tasks = len(task_list)
        if total_tasks == 0:
            self.log("Error: Nothing to process.")
            return

        self.log(f"Total tasks found: {total_tasks}")

        # 4. Execution Loop
        for i, task in enumerate(task_list):
            if not self.is_running: break
            
            try:
                self._process_single_task(task, i, total_tasks, workflow_template, output_path)
            except Exception as e:
                self.log(f"Critical Error processing task {i}: {e}")

        self.log("Batch Cycle Completed.")

    def _process_single_task(self, task: dict, index: int, total_tasks: int, workflow_template: dict, output_path: Path) -> None:
        project_dir = task["project"]
        img_path = task["image"]
        p_data = task["prompt"]
        
        self.log(f"\nProcessing [{index+1}/{total_tasks}]: {img_path.name} -> {p_data['title']}")
        
        project_out = output_path / project_dir.name
        project_out.mkdir(parents=True, exist_ok=True)
        
        clean_stem = image_utils.clean_stem(img_path.stem)
        # Subfolder per image
        image_subfolder_name = clean_stem 
        image_out_dir = project_out / image_subfolder_name
        image_out_dir.mkdir(exist_ok=True)
        
        # Step A: Upload Image
        unique_filename = f"{project_dir.name}_{img_path.name}"
        
        comfy_server_filename = self.api.upload_image(img_path, unique_filename)
        
        if not comfy_server_filename:
            self.log(f"Skipping due to upload failure (or server unavailable).")
            return

        # Step B: Prepare Workflow
        current_workflow = json.loads(json.dumps(workflow_template))
        
        # Calculate Ratio
        ratio_setting = self.settings.get("ratio", "1:1")
        current_ratio = ratio_setting
        if ratio_setting == "Manual":
            current_ratio = image_utils.get_smart_ratio(img_path)
            self.log(f">> Manual Ratio Calculated: {current_ratio}")

        # Update Nodes
        load_node_id = self.node_mapping.get("LOAD_IMAGE")
        if load_node_id in current_workflow:
            current_workflow[load_node_id]["inputs"]["image"] = comfy_server_filename or unique_filename
        
        prompt_node_id = self.node_mapping.get("GEMINI_PROMPT")
        if prompt_node_id in current_workflow:
            inputs = current_workflow[prompt_node_id]["inputs"]
            inputs["prompt"] = p_data["prompt"]
            inputs["resolution"] = self.settings.get("resolution", "1K")
            inputs["aspect_ratio"] = current_ratio
            
            if self.settings.get("use_random_seed", True):
                inputs["seed"] = int(time.time() * 1000) % 1000000000
            else:
                inputs["seed"] = self.settings.get("seed_value", 0)
                
            sys_prompt = self.settings.get("system_prompt", "")
            if sys_prompt.strip():
                inputs["system_prompt"] = sys_prompt
        
        # 3. Save Image Prefix
        # We set a temp prefix; naming.py handles the final filename after download.
        save_node_id = self.node_mapping.get("SAVE_IMAGE")
        if save_node_id in current_workflow:
            temp_prefix = f"TEMP_{clean_stem}"
            current_workflow[save_node_id]["inputs"]["filename_prefix"] = temp_prefix

        # Step C: Execution
        api_key = self.settings.get("api_key", "")
        prompt_id = self.api.queue_prompt(current_workflow, api_key)
        
        if not prompt_id:
            self.log("Failed to queue prompt.")
            return

        img_data_list = self._wait_for_completion_managed(prompt_id)
        if not img_data_list:
            self.log("Generation failed or timed out.")
            return
        
        # Download and Rename to Unified Format
        # Pass full prompt string for saving
        saved_file = self._download_and_save(img_data_list, image_out_dir, img_path.stem, p_data['title'], p_data['prompt'])
        
        if saved_file:
             self.preview_callback(str(img_path), str(saved_file), p_data['prompt'])
        
        self.progress_callback((index + 1) / total_tasks * 100)

    def _wait_for_completion_managed(self, prompt_id):
        save_node_id = self.node_mapping.get("SAVE_IMAGE")
        while self.is_running:
            hist = self.api.get_history(prompt_id)
            if hist and prompt_id in hist:
                outputs = hist[prompt_id].get("outputs", {})
                if save_node_id in outputs:
                    return outputs[save_node_id].get("images", [])
                return []
            time.sleep(1)
        return None

    def _download_and_save(self, img_data_list, image_out_dir, original_stem, prompt_title, prompt_text=None):
        last_saved = None
        for img_data in img_data_list:
            fname = img_data['filename']
            ext = Path(fname).suffix
            
            # Generate Unified Name
            target_name = naming.generate_filename(original_stem, prompt_title, ext)
            save_path = image_out_dir / target_name
            
            success = self.api.download_image(
                filename=fname,
                subfolder=img_data.get("subfolder", ""),
                img_type=img_data.get("type", "output"),
                save_path=save_path
            )
            
            if success:
                self.log(f"Saved: {save_path.name}")
                last_saved = save_path
                
                # Save Prompt Text
                if prompt_text and self.settings.get("save_logs", True):
                    txt_name = Path(target_name).stem + ".txt"
                    txt_path = image_out_dir / txt_name
                    try:
                        full_log = f"PROMPT:\n{prompt_text}"
                        txt_path.write_text(full_log, encoding="utf-8")
                    except Exception as e:
                        self.log(f"Warning: Failed to save prompt txt: {e}")
                        
        return last_saved
