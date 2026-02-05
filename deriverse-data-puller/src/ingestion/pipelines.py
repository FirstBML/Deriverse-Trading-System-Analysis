from src.ingestion.watermark import Watermark
from src.storage.writer import EventWriter
from src.common.logging import get_logger

logger = get_logger(__name__)


def run_ingestion(events: list[dict], output_dir: str):
    """
    Append-only ingestion of raw events.
    """
    watermark = Watermark()
    writer = EventWriter(output_dir)

    last_seen = watermark.load()

    ingested = 0
    for event in events:
        ts = event.get("ts")

        if last_seen is not None and ts <= last_seen:
            continue

        writer.write(event)
        watermark.update(ts)
        ingested += 1

    logger.info(f"Ingested {ingested} events")
