import pandas as pd

df = pd.read_json("data/normalized/events.jsonl", lines=True)
print(df.columns)
print(df.head(5))
