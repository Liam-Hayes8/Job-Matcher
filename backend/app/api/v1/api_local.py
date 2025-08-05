from fastapi import APIRouter
from app.api.v1.endpoints import jobs, matches
from app.api.v1.endpoints.resumes_local import router as resumes_router
from app.api.v1.endpoints.metrics import router as metrics_router

api_router = APIRouter()
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(metrics_router, tags=["metrics"])