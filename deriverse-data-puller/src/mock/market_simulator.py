import random

class MarketSimulator:
    def __init__(self, name: str, tick_size: float):
        self.name = name
        self.tick_size = tick_size
        self.price = 100.0  # starting price

    def step(self):
        """Simulate a single market tick"""
        move = random.choice([-1, 1]) * self.tick_size
        self.price += move
        return round(self.price, 2)
