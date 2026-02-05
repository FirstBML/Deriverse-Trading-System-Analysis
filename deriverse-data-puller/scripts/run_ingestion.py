# scripts/run_ingestion.py

from src.ingestion.pipelines import IngestionPipeline
from src.ingestion.watermark import WatermarkStore
from src.common.logging import get_logger
from configs.loader import load_config

logger = get_logger(__name__)


def main():
    config = load_config("configs/ingestion.yaml")

    logger.info("Starting incremental ingestion")

    watermark_store = WatermarkStore(config["checkpoint_path"])
    pipeline = IngestionPipeline(
        raw_path=config["raw_data_path"],
        analytics_path=config["analytics_staging_path"],
        watermark_store=watermark_store,
        allowed_lateness=config["allowed_lateness_seconds"],
    )

    pipeline.run()

    logger.info("Ingestion completed successfully")


if __name__ == "__main__":
    main()
