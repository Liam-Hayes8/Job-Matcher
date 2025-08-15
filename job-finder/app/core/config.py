from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application settings
    app_name: str = "job-finder"
    debug: bool = False
    
    # Database settings
    database_url: str = "postgresql://user:pass@localhost:5432/job_finder"
    
    # Vertex AI settings
    vertex_ai_project_id: str = ""
    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "textembedding-gecko@003"
    
    # ATS API settings
    greenhouse_api_key: Optional[str] = None
    lever_api_key: Optional[str] = None
    ashby_api_key: Optional[str] = None
    smartrecruiters_api_key: Optional[str] = None
    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None
    
    # Target companies for ATS APIs
    target_companies: List[str] = [
        "google", "microsoft", "amazon", "meta", "apple", "netflix", "airbnb",
        "uber", "lyft", "stripe", "square", "plaid", "robinhood", "coinbase",
        "databricks", "snowflake", "mongodb", "elastic", "confluent", "hashicorp"
    ]
    
    # Matching settings
    min_similarity_threshold: float = 0.3
    max_jobs_per_request: int = 50
    cache_ttl_hours: int = 24
    
    # HTTP settings
    request_timeout: int = 30
    max_retries: int = 3
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    class Config:
        env_file = ".env"
        env_prefix = "JOB_FINDER_"

# Load settings from environment
settings = Settings()

# Override with Secret Manager values if available
def load_secrets_from_files():
    """Load secrets from mounted Secret Manager files"""
    secrets_path = "/secrets"
    
    if os.path.exists(f"{secrets_path}/vertex-ai-key"):
        with open(f"{secrets_path}/vertex-ai-key", "r") as f:
            settings.vertex_ai_project_id = f.read().strip()
    
    if os.path.exists(f"{secrets_path}/ats-api-keys"):
        with open(f"{secrets_path}/ats-api-keys", "r") as f:
            api_keys = json.loads(f.read())
            settings.greenhouse_api_key = api_keys.get("greenhouse")
            settings.lever_api_key = api_keys.get("lever")
            settings.ashby_api_key = api_keys.get("ashby")
            settings.smartrecruiters_api_key = api_keys.get("smartrecruiters")
            settings.adzuna_app_id = api_keys.get("adzuna_app_id")
            settings.adzuna_app_key = api_keys.get("adzuna_app_key")

# Load secrets on import
try:
    import json
    load_secrets_from_files()
except Exception as e:
    print(f"Warning: Could not load secrets from files: {e}")
