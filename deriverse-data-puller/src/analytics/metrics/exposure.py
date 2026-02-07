import json
from collections import defaultdict

def build_exposure(events_path: str):
    exposure = defaultdict(lambda: {"long": 0.0, "short": 0.0})

    with open(events_path) as f:
        for line in f:
            e = json.loads(line)
            if e["event_type"] != "trade":
                continue

            side = "long" if e["side"] in ("buy", "long") else "short"
            exposure[e["market"]][side] += abs(e["size"])

    return dict(exposure)
