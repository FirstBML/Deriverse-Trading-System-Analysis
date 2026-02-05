class Watermark:
    """
    Tracks last processed block / timestamp.
    """

    def __init__(self):
        self.value = None

    def load(self):
        return self.value

    def update(self, new_value):
        self.value = new_value
