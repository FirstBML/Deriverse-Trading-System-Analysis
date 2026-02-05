class TraderSimulator:
    def __init__(self, config):
        self.config = config

    def simulate_trade(self, market_data):
        # Example: random trade based on market price
        import random
        trade = {
            "price": market_data["price"],
            "side": random.choice(["buy", "sell"]),
            "quantity": round(random.uniform(1, 10), 2),
            "timestamp": market_data["timestamp"]
        }
        return trade
