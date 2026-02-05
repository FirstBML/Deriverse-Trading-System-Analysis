from collections import defaultdict

def pnl_by_day(settles: list[dict]) -> dict:
    out = defaultdict(float)
    for s in settles:
        out[s["date"]] += s["pnl"]
    return dict(out)
