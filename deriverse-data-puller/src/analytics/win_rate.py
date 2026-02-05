def compute_win_rate(settles: list[dict]) -> float:
    wins = sum(1 for s in settles if s["pnl"] > 0)
    total = len(settles)
    return wins / total if total else 0.0
