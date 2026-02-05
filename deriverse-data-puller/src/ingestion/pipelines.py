import json
from pathlib import Path
from src.ingestion.watermark import Watermark

RAW = Path("data/raw_events.json")
OUT = Path("data/normalized")
OUT.mkdir(parents=True, exist_ok=True)

def run_ingestion():
    wm = Watermark()
    last_ts = wm.get()

    events = json.loads(RAW.read_text())
    new_events = []

    for e in events:
        if last_ts is None or e["ts"] > last_ts:
            new_events.append(e)

    if not new_events:
        print("No new events")
        return

    with open(OUT / "events.jsonl", "a") as f:
        for e in new_events:
            f.write(json.dumps(e) + "\n")

    wm.update(new_events[-1]["ts"])
    print(f"Ingested {len(new_events)} events")
