from pathlib import Path
import json

class Watermark:
    def __init__(self, path="data/watermark.json"):
        self.path = Path(path)
        if not self.path.exists():
            self._write({"last_ts": None})

    def _read(self):
        return json.loads(self.path.read_text())

    def _write(self, data):
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(json.dumps(data))

    def get(self):
        return self._read()["last_ts"]

    def update(self, ts):
        self._write({"last_ts": ts})
