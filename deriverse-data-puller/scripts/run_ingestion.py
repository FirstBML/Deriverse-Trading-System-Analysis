
# scripts/run_ingestion.py
import logging
from src.ingestion.pipelines import IngestionPipeline
from configs.loader import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting incremental ingestion")

    config = load_config("configs/ingestion.yaml")
    
    pipeline = IngestionPipeline(
        raw_path=config["raw_data_path"],
        output_path=config["normalized_output_path"],
        checkpoint_path=config["checkpoint_path"],
    )

    count = pipeline.run()
    logger.info(f"Ingested {count} new events")


if __name__ == "__main__":
    main()
