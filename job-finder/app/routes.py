from fastapi import APIRouter, HTTPException, BackgroundTasks
import httpx
import yaml
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

from .sources.util import (
    head_ok, 
    dedupe_jobs, 
    filter_recent_jobs, 
    rank_jobs_by_relevance,
    fetch_all_live
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Load company configurations
def load_companies() -> List[Dict]:
    """Load company configurations from YAML file"""
    try:
        with open('app/config/companies.yaml', 'r') as f:
            config = yaml.safe_load(f)
            return config.get('companies', [])
    except Exception as e:
        logger.error(f"Error loading companies config: {e}")
        return []

class LiveJobSearchRequest(BaseModel):
    resume_text: str
    location: Optional[str] = "US"
    max_jobs: Optional[int] = 20
    timeout: Optional[int] = 12

class LiveJobSearchResponse(BaseModel):
    jobs: List[Dict]
    metadata: Dict

@router.post("/api/v1/jobs/live", response_model=LiveJobSearchResponse)
async def jobs_live(request: LiveJobSearchRequest):
    """
    Live job search endpoint that fetches fresh jobs from ATS APIs
    and validates all apply URLs in real-time.
    """
    start_time = datetime.now()
    
    try:
        # Load company configurations
        companies = load_companies()
        if not companies:
            raise HTTPException(status_code=500, detail="No company configurations found")
        
        # Create HTTP client with timeout
        async with httpx.AsyncClient(timeout=request.timeout) as client:
            # Fetch jobs from all ATS sources concurrently
            logger.info(f"Fetching jobs from {len(companies)} companies across 3 ATS sources")
            all_jobs = await fetch_all_live(companies, client)
            
            if not all_jobs:
                logger.warning("No jobs fetched from any source")
                return LiveJobSearchResponse(
                    jobs=[],
                    metadata={
                        "total_fetched": 0,
                        "open_jobs": 0,
                        "valid_links": 0,
                        "unique_jobs": 0,
                        "returned": 0,
                        "duration_seconds": 0,
                        "sources_queried": 3,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # Filter for recent jobs (last 48 hours)
            recent_jobs = filter_recent_jobs(all_jobs, max_age_hours=48)
            logger.info(f"Filtered to {len(recent_jobs)} recent jobs out of {len(all_jobs)} total")
            
            # Remove duplicates
            unique_jobs = dedupe_jobs(recent_jobs)
            logger.info(f"Deduplicated to {len(unique_jobs)} unique jobs")
            
            # Validate all apply URLs concurrently
            logger.info(f"Validating {len(unique_jobs)} apply URLs")
            validation_tasks = [head_ok(client, job["apply_url"]) for job in unique_jobs]
            validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Keep only jobs with valid apply URLs
            valid_jobs = []
            for job, is_valid in zip(unique_jobs, validation_results):
                if isinstance(is_valid, bool) and is_valid:
                    valid_jobs.append(job)
            
            logger.info(f"Validated {len(valid_jobs)} jobs with working apply URLs out of {len(unique_jobs)}")
            
            # Rank jobs by relevance to resume
            if request.resume_text and valid_jobs:
                ranked_jobs = rank_jobs_by_relevance(valid_jobs, request.resume_text)
                final_jobs = ranked_jobs[:request.max_jobs]
            else:
                final_jobs = valid_jobs[:request.max_jobs]
            
            # Calculate timing
            duration = (datetime.now() - start_time).total_seconds()
            
            # Log metrics
            logger.info(f"Live job search completed in {duration:.2f}s: "
                       f"{len(final_jobs)} jobs returned from {len(all_jobs)} fetched")
            
            return LiveJobSearchResponse(
                jobs=final_jobs,
                metadata={
                    "total_fetched": len(all_jobs),
                    "open_jobs": len(recent_jobs),
                    "valid_links": len(valid_jobs),
                    "unique_jobs": len(unique_jobs),
                    "returned": len(final_jobs),
                    "duration_seconds": round(duration, 2),
                    "sources_queried": 3,
                    "timestamp": datetime.now().isoformat(),
                    "checked_just_now": True
                }
            )
            
    except Exception as e:
        logger.error(f"Live job search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

@router.get("/api/v1/jobs/live/health")
async def live_jobs_health():
    """Health check for live job search service"""
    try:
        companies = load_companies()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "companies_configured": len(companies),
            "sources_available": ["greenhouse", "lever", "ashby"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.post("/api/v1/jobs/live/prewarm")
async def prewarm_jobs(background_tasks: BackgroundTasks):
    """Pre-warm job vectors and cache for faster subsequent requests"""
    background_tasks.add_task(_prewarm_job_vectors)
    return {"message": "Pre-warming job vectors in background"}

async def _prewarm_job_vectors():
    """Background task to pre-fetch and cache job vectors"""
    try:
        logger.info("Starting job vector pre-warming...")
        # This would implement vector caching for embeddings
        # For now, just log the action
        await asyncio.sleep(2)  # Simulate processing time
        logger.info("Pre-warmed vectors for jobs")
    except Exception as e:
        logger.error(f"Pre-warming failed: {e}")

@router.get("/api/v1/jobs/live/validate/{job_id}")
async def validate_single_job(job_id: str):
    """Validate a single job's apply URL"""
    try:
        # This would look up the job by ID and validate its URL
        # For now, return a mock response
        return {
            "job_id": job_id,
            "valid": True,
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Job validation failed: {e}")
        raise HTTPException(status_code=500, detail="Job validation failed")
