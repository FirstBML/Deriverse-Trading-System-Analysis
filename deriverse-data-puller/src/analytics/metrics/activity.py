from collections import defaultdict
import json

def activity_by_product(events_path: str):
    stats = defaultdict(lambda: {
        "trades": 0,
        "volume": 0.0,
        "fees": 0.0
    })

    with open(events_path) as f:
        for line in f:
            e = json.loads(line)
            p = e["product_type"]

            stats[p]["trades"] += 1
            stats[p]["volume"] += abs(e["price"] * e["size"])
            stats[p]["fees"] += e.get("fee", 0.0)

    return stats
