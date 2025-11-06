"""simple persistent memory for retrieval seeds.

this lightweight store keeps successes and failures keyed by a short signature of the task text.
"""
import json
import hashlib
from pathlib import Path
from typing import List


class MemoryStore:
    def __init__(self, path: str = "~/.nyuctf_memory.json"):
        self.path = Path(path).expanduser()
        # ensure file exists
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("{}")
        try:
            self.db = json.loads(self.path.read_text() or "{}")
        except Exception:
            self.db = {}

    def _write(self) -> None:
        # persist the current db to disk
        self.path.write_text(json.dumps(self.db, indent=2))

    def sig(self, text: str) -> str:
        # derive a short signature for the text (not cryptographic)
        return hashlib.md5(text.encode()).hexdigest()[:10]

    def get(self, text: str) -> List[str]:
        # return successful queries associated with this text
        return self.db.get(self.sig(text), {}).get("success", [])

    def add_success(self, text: str, query: str) -> None:
        key = self.sig(text)
        self.db.setdefault(key, {"success": [], "fail": []})
        if query not in self.db[key]["success"]:
            self.db[key]["success"].append(query)
            self._write()

    def add_fail(self, text: str, query: str) -> None:
        key = self.sig(text)
        self.db.setdefault(key, {"success": [], "fail": []})
        if query not in self.db[key]["fail"]:
            self.db[key]["fail"].append(query)
            self._write()
