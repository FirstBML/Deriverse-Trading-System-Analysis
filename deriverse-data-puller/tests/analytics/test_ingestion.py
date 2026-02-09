# Create a test script test_ingestion.py
import json

with open("data/normalized/events.jsonl", "r") as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if line:
            try:
                data = json.loads(line)
                print(f"Line {i}: OK - {data.get('event_type', 'N/A')}")
            except json.JSONDecodeError as e:
                print(f"Line {i}: ERROR - {e}")
                print(f"  Content: {line[:50]}...")
        else:
            print(f"Line {i}: EMPTY LINE")