# scripts/launch_dashboard.py

import streamlit as st
from dashboards.app import run_app
from src.common.logging import get_logger
from configs.loader import load_config

logger = get_logger(__name__)


def main():
    config = load_config("configs/dashboard.yaml")

    logger.info("Launching analytics dashboard")

    st.set_page_config(
        page_title="Deriverse Trading Analytics",
        layout="wide"
    )

    run_app(config)


if __name__ == "__main__":
    main()
