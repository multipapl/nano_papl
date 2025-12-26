import json
import os
import uuid
import datetime
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

    def _get_path(self, session_id):
        return self.base_dir / f"{session_id}.json"

    def create_session(self):
        """Creates a new empty session ID."""
        session_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        data = {
            "id": session_id,
            "title": "New Chat",
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": []
        }
        self.save_session(session_id, data)
        return session_id, data

    def save_session(self, session_id, data):
        """Saves session data to JSON."""
        # Update timestamp
        data["updated_at"] = datetime.datetime.now().isoformat()
        
        # Auto-title if "New Chat" and messages exist
        if data["title"] == "New Chat" and data["messages"]:
            first_msg = data["messages"][0]["text"]
            # Take first 30 chars or first line
            title = first_msg.split('\n')[0][:30]
            if len(first_msg) > 30: title += "..."
            data["title"] = title

        with open(self._get_path(session_id), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_session(self, session_id):
        """Loads a session by ID."""
        path = self._get_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def list_sessions(self):
        """Returns a list of sessions sorted by last update."""
        sessions = []
        for f in self.base_dir.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    sessions.append({
                        "id": data.get("id", f.stem),
                        "title": data.get("title", "Untitled"),
                        "updated_at": data.get("updated_at", "")
                    })
            except:
                continue
        
        # Sort by updated_at desc
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions

    def delete_session(self, session_id):
        path = self._get_path(session_id)
        if path.exists():
            path.unlink()
