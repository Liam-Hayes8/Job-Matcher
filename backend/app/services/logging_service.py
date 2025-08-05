import logging
import os
from google.cloud import logging as cloud_logging

def setup_logging():
    if os.getenv("ENVIRONMENT") == "production":
        client = cloud_logging.Client()
        client.setup_logging()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )