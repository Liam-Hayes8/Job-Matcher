import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings
from app.services.secret_service import get_secret
import json
import logging

logger = logging.getLogger(__name__)

_firebase_app = None

def get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        try:
            firebase_config_json = get_secret(settings.FIREBASE_CONFIG_SECRET_NAME)
            firebase_config = json.loads(firebase_config_json)
            
            cred = credentials.Certificate(firebase_config)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase app initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase app: {e}")
            raise
    
    return _firebase_app

async def verify_firebase_token(token: str) -> str:
    try:
        get_firebase_app()
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        return user_id
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise ValueError("Invalid authentication token")