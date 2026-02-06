from typing import List, Dict
from collections import defaultdict

def build_win_rate(pnls: List[Dict]) -> Dict[str, float]:
    wins = defaultdict(int)
    total = defaultdict(int)

    for p in pnls:
        trader = p["trader"]
        total[trader] += 1
        if p["pnl"] > 0:
            wins[trader] += 1

    return {
        t: wins[t] / total[t] if total[t] else 0
        for t in total
    }
