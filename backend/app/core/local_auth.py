import logging
import os

logger = logging.getLogger(__name__)

async def verify_firebase_token_local(token: str) -> str:
    """Mock Firebase token verification for local development."""
    if os.getenv("ENVIRONMENT") == "development":
        # Return a mock user ID for local development
        logger.info("Using mock Firebase authentication for local development")
        return "local-user-123"
    
    # For production, use the real Firebase verification
    from app.core.auth import verify_firebase_token
    return await verify_firebase_token(token)