from google.cloud import secretmanager
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_secret(secret_name: str) -> str:
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{settings.PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise