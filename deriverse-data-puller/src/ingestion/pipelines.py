# src/ingestion/pipelines.py
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
        """
        Event-driven ingestion: normalize once, append forever.
        Supports both JSON array and JSONL formats.
        """
        if not self.raw_path.exists():
            raise FileNotFoundError(f"Raw data source not found: {self.raw_path}")

        # Load events based on file format
        if self.raw_path.suffix == '.json':
            # JSON array format (e.g., configs/mock_data.json)
            with self.raw_path.open("r", encoding="utf-8") as f:
                raw_events = json.load(f)
        elif self.raw_path.suffix == '.jsonl':
            # JSONL format (one JSON object per line)
            raw_events = []
            with self.raw_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        raw_events.append(json.loads(line))
        else:
            raise ValueError(f"Unsupported file format: {self.raw_path.suffix}")

        new_events = []
        errors = []

        for idx, raw in enumerate(raw_events, 1):
            try:
                # Generate event_id if missing
                if "event_id" not in raw:
                    seed = (
                        f"{raw.get('event_type')}|"
                        f"{raw.get('timestamp')}|"
                        f"{raw.get('trader_id')}|"
                        f"{raw.get('market_id')}|{idx}"
                    )
                    raw["event_id"] = hashlib.sha256(seed.encode()).hexdigest()

                # Skip if already processed
                if not self.watermark.is_new(raw["event_id"]):
                    continue

                # Normalize and validate
                normalized = normalize_event(raw)
                validate_event(normalized)

                new_events.append(normalized)
                self.watermark.mark(raw["event_id"])

            except EventValidationError as e:
                errors.append(f"Event {idx}: Validation failed - {e}")
            except Exception as e:
                errors.append(f"Event {idx}: Unexpected error - {e}")

        # Report errors
        if errors:
            print(f"⚠️  {len(errors)} events had issues:")
            for e in errors[:5]:
                print(f"   - {e}")
            if len(errors) > 5:
                print(f"   ... and {len(errors) - 5} more")

        # Write normalized events to output (JSONL format)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a", encoding="utf-8") as f:
            for e in new_events:
                f.write(json.dumps(e) + "\n")

        print(f"✅ Ingested {len(new_events)} valid events")
        return len(new_events)