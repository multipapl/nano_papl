import json
import os
import uuid
import datetime
import shutil
from pathlib import Path

class HistoryManager:
    def __init__(self, base_dir=None):
        if base_dir is None:
            # Default to User Documents/NanoPapl/History
            docs = Path(os.path.expanduser("~")) / "Documents" / "NanoPapl" / "History"
            self.base_dir = docs
        else:
            self.base_dir = Path(base_dir)
            
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, session_id, folder_name=None):
        """Returns the file path for a session. 
        If folder_name is provided (even if empty string for root), use it.
        If folder_name is None, search recursively (useful for loading).
        """
        if folder_name is not None:
            if folder_name:
                folder_path = self.base_dir / folder_name
                folder_path.mkdir(parents=True, exist_ok=True)
                return folder_path / f"{session_id}.json"
            else:
                return self.base_dir / f"{session_id}.json"
        
        # Search for existing file if folder is unknown (loading case)
        for p in self.base_dir.rglob(f"{session_id}.json"):
            return p
            
        return self.base_dir / f"{session_id}.json"

    def create_session(self, folder_name=""):
        """Creates a new empty session ID."""
        session_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        data = {
            "id": session_id,
            "title": "New Chat",
            "folder": folder_name,
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": []
        }
        self.save_session(session_id, data, folder_name)
        return session_id, data

    def save_session(self, session_id, data, folder_name=None):
        """Saves session data to JSON."""
        # Update timestamp
        data["updated_at"] = datetime.datetime.now().isoformat()
        
        # Use folder from data if not provided (safety)
        if folder_name is None:
            folder_name = data.get("folder", "")
            
        # Auto-title if "New Chat" and messages exist
        if data["title"] == "New Chat" and data["messages"]:
            first_msg = data["messages"][0]["text"]
            # Take first 30 chars or first line
            title = first_msg.split('\n')[0][:30]
            if len(first_msg) > 30: title += "..."
            data["title"] = title
            
        path = self._get_path(session_id, folder_name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_session(self, session_id):
        """Loads a session by ID searching recursively."""
        path = self._get_path(session_id)
        if not path or not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def list_sessions(self):
        """Returns a nested structure of folders and sessions."""
        structure = {"folders": {}, "sessions": []}
        
        # 1. Initialize folders from physical directories (to show empty folders)
        for d in self.base_dir.iterdir():
            if d.is_dir():
                structure["folders"][d.name] = []

        # 2. Fill with sessions
        # Use rglob to find all sessions including those in folders
        for f in self.base_dir.rglob("*.json"):
            try:
                # Determine folder relative to base_dir
                rel_path = f.parent.relative_to(self.base_dir)
                folder_name = str(rel_path) if str(rel_path) != "." else ""
                
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    session_info = {
                        "id": data.get("id", f.stem),
                        "title": data.get("title", "Untitled"),
                        "updated_at": data.get("updated_at", ""),
                        "folder": folder_name
                    }
                    
                    if folder_name:
                        if folder_name not in structure["folders"]:
                            structure["folders"][folder_name] = []
                        structure["folders"][folder_name].append(session_info)
                    else:
                        structure["sessions"].append(session_info)
            except:
                continue
        
        # Sort internal lists by updated_at desc
        structure["sessions"].sort(key=lambda x: x["updated_at"], reverse=True)
        for folder in structure["folders"]:
            structure["folders"][folder].sort(key=lambda x: x["updated_at"], reverse=True)
            
        return structure

    def create_folder(self, folder_name):
        """Create a physical folder in history directory."""
        if not folder_name: return
        (self.base_dir / folder_name).mkdir(parents=True, exist_ok=True)

    def move_session(self, session_id, target_folder):
        """Move session file to another folder."""
        old_path = self._get_path(session_id)
        if not old_path or not old_path.exists():
            return False
            
        new_path = self._get_path(session_id, target_folder)
        
        # If folder changed, move file
        if old_path != new_path:
            try:
                with open(old_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data["folder"] = target_folder
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                old_path.unlink()
                return True
            except:
                return False
        return True

    def get_folders(self):
        """Returns list of folder names."""
        return [str(d.relative_to(self.base_dir)) for d in self.base_dir.iterdir() if d.is_dir()]

    def delete_session(self, session_id: str) -> None:
        """Permanently delete a session file."""
        path = self._get_path(session_id)
        if path and path.exists():
            path.unlink()

    def delete_folder(self, folder_name: str) -> None:
        """Recursively delete folder and all contents."""
        if not folder_name: return
        folder_path = self.base_dir / folder_name
        if folder_path.exists() and folder_path.is_dir():
            shutil.rmtree(folder_path)
