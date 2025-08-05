from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.auth import verify_firebase_token
from app.services.logging_service import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Job Matcher API")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down Job Matcher API")

app = FastAPI(
    title="Job Matcher API",
    description="Resume parsing and job matching service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

@app.middleware("http")
async def auth_middleware(request, call_next):
    if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
        response = await call_next(request)
        return response
    
    try:
        authorization: HTTPAuthorizationCredentials = await security(request)
        if authorization:
            token = authorization.credentials
            user_id = await verify_firebase_token(token)
            request.state.user_id = user_id
    except Exception as e:
        logger.warning(f"Auth middleware error: {e}")
        request.state.user_id = None
    
    response = await call_next(request)
    return response

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Job Matcher API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )