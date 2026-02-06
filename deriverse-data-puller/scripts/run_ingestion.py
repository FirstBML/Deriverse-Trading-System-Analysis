# scripts/run_ingestion.py
from configs.loader import load_config
from src.ingestion.pipelines import IngestionPipeline
from src.common.logging import get_logger

log = get_logger(__name__)

def main():
    log.info("Starting incremental ingestion")

    config = load_config("ingestion.yaml")

    pipeline = IngestionPipeline(
        raw_path=config["raw_data_path"],
        output_path=config["normalized_output_path"],
        checkpoint_path=config["checkpoint_path"],
    )

    count = pipeline.run()
    log.info(f"Ingested {count} new events")

if __name__ == "__main__":
    main()
