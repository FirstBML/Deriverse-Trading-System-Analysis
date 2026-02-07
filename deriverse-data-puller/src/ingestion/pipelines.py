import json
import hashlib
from pathlib import Path
from src.ingestion.watermark import WatermarkStore
from src.ingestion.normalizer import normalize_event
from src.analytics.validate import validate_event, EventValidationError


class IngestionPipeline:
    def __init__(self, raw_path: str, output_path: str, checkpoint_path: str):
        self.raw_path = Path(raw_path)
        self.output_path = Path(output_path)
        self.watermark = WatermarkStore(checkpoint_path)

    def run(self) -> int:
        if not self.raw_path.exists():
            raise FileNotFoundError(f"Raw data source not found: {self.raw_path}")

        events = json.loads(self.raw_path.read_text())
        new_events = []
        errors = []

        for idx, raw in enumerate(events):
            try:
                # Stable deterministic event_id
                if "event_id" not in raw:
                    seed = f"{raw.get('event_type')}|{raw.get('ts')}|{raw.get('trader')}|{raw.get('market')}|{idx}"
                    raw["event_id"] = hashlib.sha256(seed.encode()).hexdigest()

                if not self.watermark.is_new(raw["event_id"]):
                    continue

                normalized = normalize_event(raw)
                validate_event(normalized)

                new_events.append(normalized)
                self.watermark.mark(raw["event_id"])

            except EventValidationError as e:
                errors.append(f"Event {idx} failed validation: {e}")

        if errors:
            print(f"⚠️  {len(errors)} events failed validation and were skipped:")
            for e in errors[:5]:
                print(f"   - {e}")
            if len(errors) > 5:
                print(f"   ... and {len(errors) - 5} more")

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a", encoding="utf-8") as f:
            for e in new_events:
                f.write(json.dumps(e) + "\n")

        print(f"✅ Ingested {len(new_events)} valid events")
        return len(new_events)
