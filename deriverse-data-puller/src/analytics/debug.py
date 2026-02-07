import json
from pathlib import Path
from collections import Counter

def inspect_normalized_data():
    normalized_path = Path("data/normalized/events.jsonl")

    if not normalized_path.exists():
        print("❌ No normalized data file found.")
        return

    if normalized_path.stat().st_size == 0:
        print("⚠️ Normalized file exists but is empty.")
        return

    all_fields = set()
    event_types = Counter()
    sample_events = []

    with normalized_path.open() as f:
        for i, line in enumerate(f):
            event = json.loads(line)
            all_fields.update(event.keys())
            event_types[event.get("event_type")] += 1

            if i < 3:
                sample_events.append(event)

    print("\n📊 Normalized Data Overview")
    print(f"Total events: {sum(event_types.values())}")

    print("\nEvent types:")
    for et, c in event_types.items():
        print(f"  - {et}: {c}")

    print("\nColumns present:")
    for field in sorted(all_fields):
        print(f"  - {field}")

    print("\nSample events:")
    for i, ev in enumerate(sample_events, 1):
        print(f"\nEvent {i}")
        for k, v in ev.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    inspect_normalized_data()
