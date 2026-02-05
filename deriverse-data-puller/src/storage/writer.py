class EventWriter:
    def __init__(self, config):
        self.config = config

    def write(self, events):
        # Example: write to a local JSON file
        import json
        with open("mock_events.json", "w") as f:
            json.dump(events, f, indent=2)
