import json
import time
from pathlib import Path

from core.comfy_api import ComfyAPI
from core.utils.path_provider import PathProvider
from core.utils import prompt_parser, image_utils

# Default Mapping
DEFAULT_NODE_MAPPING = {
    "LOAD_IMAGE": "11",
    "GEMINI_PROMPT": "35",
    "SAVE_IMAGE": "30"
}

class ComfyOrchestrator:
    """
    Orchestrates the batch processing of images through ComfyUI.
    Handles project scanning, task creation, and execution flow.
    """
    def __init__(self, settings, log_callback=None, progress_callback=None, node_mapping=None):
        self.settings = settings
        self.log_callback = log_callback or (lambda x: None)
        self.progress_callback = progress_callback or (lambda x: None)
        
        self.api = ComfyAPI(base_url=settings.get("comfy_url", "http://127.0.0.1:8188"))
        self.is_running = True
        self.project_provider = PathProvider() 
        
        # Dynamic Node Mapping
        self.node_mapping = node_mapping or DEFAULT_NODE_MAPPING

    def log(self, message):
        self.log_callback(message)

    def stop(self):
        self.is_running = False

    def process_batch(self):
        # Input path from settings (UI) or PathProvider?
        # UI passes 'input_path' and 'output_path'. We respect those but fall back to defaults?
        input_path_str = self.settings.get("input_path", "")
        output_path_str = self.settings.get("output_path", "")
        
        input_path = Path(input_path_str) if input_path_str else self.project_provider.get_default_projects_path()
        output_path = Path(output_path_str) if output_path_str else self.project_provider.get_renders_dir(input_path) # Default to _renders if not set?
        
        workflow_path = self.settings.get("workflow_path", "")
        dry_run = self.settings.get("dry_run", False)
        
        self.log(f"--- Starting ComfyUI Batch ---")
        self.log(f"Mode: {'DRY RUN (No Generation)' if dry_run else 'LIVE GENERATION'}")

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

        valid_exts = ('.png', '.jpg', '.jpeg', '.webp')

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
                self._process_single_task(task, i, total_tasks, workflow_template, output_path, dry_run)
            except Exception as e:
                self.log(f"Critical Error processing task {i}: {e}")

        self.log("Batch Cycle Completed.")

    def _process_single_task(self, task, index, total_tasks, workflow_template, output_path, dry_run):
        project_dir = task["project"]
        img_path = task["image"]
        p_data = task["prompt"]
        
        self.log(f"\nProcessing [{index+1}/{total_tasks}]: {img_path.name} -> {p_data['title']}")
        
        project_out = output_path / project_dir.name
        project_out.mkdir(parents=True, exist_ok=True)
        
        clean_stem = img_path.stem.replace("_optimized", "")
        image_subfolder_name = clean_stem 
        image_out_dir = project_out / image_subfolder_name
        image_out_dir.mkdir(exist_ok=True)
        
        # Step A: Upload Image
        unique_filename = f"{project_dir.name}_{img_path.name}"
        
        comfy_server_filename = self.api.upload_image(img_path, unique_filename)
        
        if not comfy_server_filename:
            self.log(f"Skipping due to upload failure (or server unavailable).")
            # If dry run, maybe continue? But upload failing implies server issue.
            if not dry_run: return

        # Step B: Prepare Workflow
        current_workflow = json.loads(json.dumps(workflow_template))
        
        # Calculate Ratio
        ratio_setting = self.settings.get("ratio", "1:1")
        current_ratio = ratio_setting
        if ratio_setting == "Manual":
            current_ratio = image_utils.get_smart_ratio(img_path)
            self.log(f">> Manual Ratio Calculated: {current_ratio}")

        # Update Nodes using Dynamic Mapping
        # 1. Load Image
        load_node_id = self.node_mapping.get("LOAD_IMAGE")
        if load_node_id in current_workflow:
            current_workflow[load_node_id]["inputs"]["image"] = comfy_server_filename or unique_filename
        
        # 2. Prompt / Settings
        prompt_node_id = self.node_mapping.get("GEMINI_PROMPT")
        if prompt_node_id in current_workflow:
            inputs = current_workflow[prompt_node_id]["inputs"]
            inputs["prompt"] = p_data["prompt"]
            inputs["resolution"] = self.settings.get("resolution", "1K")
            inputs["aspect_ratio"] = current_ratio
            
            # Seed
            if self.settings.get("use_random_seed", True):
                inputs["seed"] = int(time.time() * 1000) % 1000000000
            else:
                inputs["seed"] = self.settings.get("seed_value", 0)
                
            # System Prompt
            sys_prompt = self.settings.get("system_prompt", "")
            if sys_prompt.strip():
                inputs["system_prompt"] = sys_prompt
        
        # 3. Save Image Prefix
        save_node_id = self.node_mapping.get("SAVE_IMAGE")
        if save_node_id in current_workflow:
            clean_title = p_data['title'].replace("_+_", "+").replace(" + ", "+")
            prefix = f"{clean_stem}_{clean_title}"
            current_workflow[save_node_id]["inputs"]["filename_prefix"] = prefix

        # Step C: Execution / Dry Run
        if dry_run:
            self.log(f">> DRY RUN: Uploaded {unique_filename}")
            self.log(f">> Ratio: {current_ratio}")
            self.progress_callback((index + 1) / total_tasks * 100)
            time.sleep(0.1)
            return

        # LIVE
        api_key = self.settings.get("api_key", "")
        if not api_key:
             self.log("ERROR: ComfyUI API Key not set!")
             return 
             
        prompt_id = self.api.queue_prompt(current_workflow, api_key)
        if not prompt_id:
            self.log("Failed to queue prompt.")
            return

        img_data_list = self._wait_for_completion_managed(prompt_id)
        if not img_data_list:
            self.log("Generation failed or timed out.")
            return
        
        self._download_and_save(img_data_list, image_out_dir, clean_stem, p_data['title'])
        
        self.progress_callback((index + 1) / total_tasks * 100)

    def _wait_for_completion_managed(self, prompt_id):
        # Polling logic
        save_node_id = self.node_mapping.get("SAVE_IMAGE")
        
        while self.is_running:
            hist = self.api.get_history(prompt_id)
            if hist and prompt_id in hist:
                outputs = hist[prompt_id].get("outputs", {})
                if save_node_id in outputs:
                    return outputs[save_node_id].get("images", [])
                # If finished but no images in expected node, check elsewhere or return empty
                return []
            time.sleep(1)
        return None

    def _download_and_save(self, img_data_list, image_out_dir, clean_stem, raw_title):
        for img_data in img_data_list:
            fname = img_data['filename']
            ext = Path(fname).suffix
            
            self.log(f">> Debug: Downloading {fname} | Subfolder: {img_data.get('subfolder')} | Type: {img_data.get('type')}")
            
            clean_title = raw_title.replace("_+_", "+").replace(" + ", "+")
            timestamp = int(time.time())
            target_name = f"{clean_stem}_{clean_title}_{timestamp}{ext}"
            save_path = image_out_dir / target_name
            
            success = self.api.download_image(
                filename=fname,
                subfolder=img_data.get("subfolder", ""),
                img_type=img_data.get("type", "output"),
                save_path=save_path
            )
            
            if success:
                self.log(f"Saved: {save_path.name}")
