from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import logging
import os
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api_local import api_router
from app.services.logging_service_local import setup_logging
# Import models to ensure they are registered with SQLAlchemy
from app.models import resume

setup_logging()
logger = logging.getLogger(__name__)

# Mock authentication for local development
async def mock_verify_token(token: str) -> str:
    logger.info("Using mock authentication for local development")
    return "local-user-123"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Job Matcher API (Local)")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down Job Matcher API (Local)")

app = FastAPI(
    title="Job Matcher API (Local)",
    description="Resume parsing and job matching service - Local Development",
    version="1.0.0-local",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

@app.middleware("http")
async def auth_middleware(request, call_next):
    # Skip auth for health checks and docs
    if request.url.path in ["/", "/health", "/docs", "/openapi.json", "/metrics"]:
        response = await call_next(request)
        return response
    
    # Mock authentication for local development
    request.state.user_id = "local-user-123"
    response = await call_next(request)
    return response

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Job Matcher API - Local Development", "version": "1.0.0-local"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": "local"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main_local:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )