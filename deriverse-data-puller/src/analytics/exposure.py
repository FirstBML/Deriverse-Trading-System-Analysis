def compute_exposure(events: list[dict]) -> float:
    """
    Gross exposure approximation.
    """
    return sum(abs(e.get("size", 0)) for e in events)
