def compute_fees(events: list[dict]) -> float:
    return sum(e.get("fee", 0.0) for e in events)
