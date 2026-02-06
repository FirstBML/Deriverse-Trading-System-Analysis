# src/ingestion/pipelines.py
import json
import hashlib
from pathlib import Path
from typing import List, Dict
from src.ingestion.watermark import WatermarkStore

class IngestionPipeline:
    def __init__(self, raw_path, output_path, checkpoint_path):
        self.raw_path = Path(raw_path)
        self.output_path = Path(output_path)
        self.watermark = WatermarkStore(checkpoint_path)

    def run(self) -> int:
        events = json.loads(self.raw_path.read_text())

        new_events = []
        
        for idx, e in enumerate(events):
            # Derive a stable event_id if missing
            event_id = e.get("event_id")

            if event_id is None:
                raw = f"{e.get('event_type')}|{e.get('timestamp')}|{e.get('trader')}|{e.get('market')}|{idx}"
                event_id = hashlib.sha256(raw.encode()).hexdigest()
                e["event_id"] = event_id

            if self.watermark.is_new(event_id):
                new_events.append(e)
                self.watermark.mark(event_id)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a") as f:
            for e in new_events:
                f.write(json.dumps(e) + "\n")

        return len(new_events)
