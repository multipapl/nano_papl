import json
import uuid
import requests
from core.logger import logger

class ComfyAPI:
    """
    Handles HTTP communication with the ComfyUI server using the requests library.
    """
    def __init__(self, base_url="http://127.0.0.1:8188"):
        self.base_url = base_url.rstrip('/')
        self.client_id = str(uuid.uuid4())

    def upload_image(self, file_path: str, target_name: str) -> str | None:
        """
        Uploads an image to the ComfyUI server.

        Args:
            file_path (str): The local path to the image file.
            target_name (str): The filename to be used on the server.

        Returns:
            str | None: The filename on the server if successful, None otherwise.
        """
        url = f"{self.base_url}/upload/image"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'image': (target_name, f, 'image/png')} # Basic MIME, requests handles boundary
                # ComfyUI might expect 'overwrite': 'true' or similar if needed.
                data = {'overwrite': 'true'} 
                
                response = requests.post(url, files=files, data=data)
                
            if response.status_code == 200:
                result = response.json()
                return result.get("name")
            else:
                logger.error(f"[ComfyAPI] Upload failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"[ComfyAPI] Upload error: {e}")
            return None

    def queue_prompt(self, workflow: dict, api_key: str = None) -> str | None:
        """
        Queues a workflow prompt on the ComfyUI server.

        Args:
            workflow (dict): The workflow dictionary (JSON-compatible).
            api_key (str, optional): API Key if authentication is required.

        Returns:
            str | None: The prompt ID if successful, None otherwise.
        """
        url = f"{self.base_url}/prompt"
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }

        if api_key:
            payload["extra_data"] = {
                "api_key_comfy_org": api_key
            }

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return response.json().get("prompt_id")
            else:
                logger.error(f"[ComfyAPI] Queue prompt failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"[ComfyAPI] Queue prompt error: {e}")
            return None

    def get_history(self, prompt_id):
        """
        Retrieves history for a specific prompt_id.
        Returns history dict or None.
        """
        url = f"{self.base_url}/history/{prompt_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            logger.error(f"[ComfyAPI] History error: {e}")
            return None

    def download_image(self, filename, subfolder, img_type, save_path):
        """
        Downloads a generated image.
        Returns True on success, False on failure.
        """
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": img_type
        }
        
        url = f"{self.base_url}/view"
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                logger.error(f"[ComfyAPI] Download failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"[ComfyAPI] Download error: {e}")
            return False
