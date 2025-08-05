import logging
import os

def setup_logging():
    """Setup basic logging for local development."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging configured for local development")