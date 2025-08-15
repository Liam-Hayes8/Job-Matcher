from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

from app.models import JobRequest, JobResponse, JobMatch
from app.services.embedding_service import EmbeddingService
from app.services.ats_service import ATSService
from app.services.matching_service import MatchingService
from app.core.config import settings
from app.core.database import get_db, DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Job Finder Service",
    description="Live job matching service with ATS integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
embedding_service = EmbeddingService()
ats_service = ATSService()
matching_service = MatchingService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await embedding_service.initialize()
        await ats_service.initialize()
        await matching_service.initialize()
        logger.info("Job Finder Service started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/jobs/live", response_model=List[JobResponse])
async def find_live_jobs(
    request: JobRequest,
    db: DatabaseManager = Depends(get_db)
):
    """
    Find live job matches for a resume
    
    This endpoint:
    1. Extracts skills and experience from resume text
    2. Fetches live job postings from multiple ATS APIs
    3. Generates embeddings for resume and job descriptions
    4. Calculates similarity scores and ranks matches
    5. Returns only fresh, valid job postings with canonical apply URLs
    """
    try:
        logger.info(f"Processing job match request for location: {request.location}")
        
        # 1. Generate resume embedding
        resume_embedding = await embedding_service.embed_text(request.resume_text)
        
        # 2. Fetch live job postings from ATS APIs
        async with httpx.AsyncClient(timeout=30.0) as client:
            jobs = await ats_service.fetch_live_jobs(
                client=client,
                location=request.location,
                days=request.days,
                keywords=request.keywords
            )
        
        if not jobs:
            logger.warning("No live jobs found from ATS APIs")
            return []
        
        # 3. Filter for recent and valid postings
        valid_jobs = []
        for job in jobs:
            if await ats_service.is_job_valid(client, job):
                valid_jobs.append(job)
        
        logger.info(f"Found {len(valid_jobs)} valid jobs out of {len(jobs)} total")
        
        # 4. Generate embeddings for job descriptions
        job_embeddings = await embedding_service.embed_jobs(valid_jobs)
        
        # 5. Calculate similarity scores and rank matches
        matches = await matching_service.rank_jobs(
            resume_embedding=resume_embedding,
            jobs=valid_jobs,
            job_embeddings=job_embeddings,
            limit=request.limit
        )
        
        # 6. Store job embeddings for future reuse
        await db.store_job_embeddings(valid_jobs, job_embeddings)
        
        # 7. Format response
        responses = []
        for match in matches:
            response = JobResponse(
                id=match["id"],
                title=match["title"],
                company=match["company"],
                description=match["description"],
                location=match["location"],
                apply_url=match["apply_url"],
                posted_at=match["posted_at"],
                match_score=match["match_score"],
                matching_skills=match["matching_skills"],
                salary_min=match.get("salary_min"),
                salary_max=match.get("salary_max"),
                job_type=match.get("job_type"),
                remote=match.get("remote", False)
            )
            responses.append(response)
        
        logger.info(f"Returning {len(responses)} job matches")
        return responses
        
    except Exception as e:
        logger.error(f"Error in find_live_jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find job matches: {str(e)}")

@app.get("/jobs/cached", response_model=List[JobResponse])
async def get_cached_jobs(
    resume_text: str,
    location: str = "US",
    limit: int = 20,
    db: DatabaseManager = Depends(get_db)
):
    """
    Get job matches from cached embeddings (faster but may be stale)
    """
    try:
        # Generate resume embedding
        resume_embedding = await embedding_service.embed_text(resume_text)
        
        # Get cached jobs and embeddings
        cached_jobs = await db.get_cached_jobs(location=location, limit=100)
        
        if not cached_jobs:
            return []
        
        # Calculate similarity scores
        matches = await matching_service.rank_cached_jobs(
            resume_embedding=resume_embedding,
            cached_jobs=cached_jobs,
            limit=limit
        )
        
        return [JobResponse(**match) for match in matches]
        
    except Exception as e:
        logger.error(f"Error in get_cached_jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cached jobs: {str(e)}")

@app.post("/jobs/refresh")
async def refresh_job_cache(
    location: str = "US",
    db: DatabaseManager = Depends(get_db)
):
    """
    Refresh the job cache by fetching new postings from ATS APIs
    This endpoint is typically called by a scheduled job
    """
    try:
        logger.info(f"Starting job cache refresh for location: {location}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Fetch fresh jobs
            jobs = await ats_service.fetch_live_jobs(
                client=client,
                location=location,
                days=7,  # Cache jobs from last 7 days
                keywords=None
            )
            
            # Generate embeddings
            job_embeddings = await embedding_service.embed_jobs(jobs)
            
            # Store in database
            await db.store_job_embeddings(jobs, job_embeddings)
            
            logger.info(f"Successfully refreshed cache with {len(jobs)} jobs")
            return {"status": "success", "jobs_refreshed": len(jobs)}
            
    except Exception as e:
        logger.error(f"Error in refresh_job_cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh job cache: {str(e)}")

@app.get("/stats")
async def get_service_stats():
    """Get service statistics"""
    try:
        stats = {
            "total_jobs_cached": await matching_service.get_cached_job_count(),
            "ats_services_available": ats_service.get_available_services(),
            "embedding_model": embedding_service.get_model_info(),
            "last_cache_refresh": await matching_service.get_last_refresh_time()
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service stats")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
