import os
from app.core.config import Settings

class LocalSettings(Settings):
    DEBUG: bool = True
    
    # Override for local development
    def get_database_url(self) -> str:
        return os.getenv("DATABASE_URL", "postgresql://job_matcher_user:local_dev_password@localhost:5432/job_matcher")
    
    # Mock Firebase for local development
    FIREBASE_PROJECT_ID: str = "demo-project"
    
    # Disable secret manager for local dev
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if os.getenv("ENVIRONMENT") == "development":
            self.DEBUG = True