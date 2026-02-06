# src/ingestion/watermark.py
import json
from pathlib import Path
from typing import Set

class WatermarkStore:
    """
    Persistent watermark store to prevent reprocessing events.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.seen: Set[str] = set()
        self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, "r") as f:
                self.seen = set(json.load(f))

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(list(self.seen), f)

    def is_new(self, event_id: str) -> bool:
        return event_id not in self.seen

    def mark(self, event_id: str):
        self.seen.add(event_id)
        self._save()
