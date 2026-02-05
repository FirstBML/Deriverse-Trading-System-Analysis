import streamlit as st
import json

st.title("Deriverse Mock Trading Dashboard")

try:
    with open("mock_events.json", "r") as f:
        events = json.load(f)
except FileNotFoundError:
    st.warning("No mock events found. Run `generate_mock_data.py` first.")
    events = []

if events:
    st.write(f"Total events: {len(events)}")
    st.dataframe(events)
