from fastapi import APIRouter
from app.api.v1.endpoints import resumes, jobs, matches, metrics

api_router = APIRouter()
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(metrics.router, tags=["metrics"])