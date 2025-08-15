from fastapi import APIRouter, HTTPException, BackgroundTasks
import asyncio
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import yaml
import os
from .sources import greenhouse, lever, ashby, smartrecruiters, adzuna
from .util import head_ok, embed_resume, embed_jobs, rank, dedupe_jobs

logger = logging.getLogger(__name__)
router = APIRouter()

# Load company configurations
def load_companies():
    companies_file = "backend/app/routes/companies.yaml"
    if os.path.exists(companies_file):
        with open(companies_file, 'r') as f:
            return yaml.safe_load(f)
    return {}

@router.post("/api/v1/jobs/live")
async def jobs_live(
    resume_text: str, 
    location: str = "US",
    max_jobs: int = 50,
    timeout: int = 12
):
    """
    Fetch live jobs from canonical ATS APIs with real-time link validation.
    Returns fresh, valid job postings ranked by relevance to the resume.
    """
    start_time = datetime.now()
    companies = load_companies()
    
    try:
        # Fetch jobs from multiple sources in parallel
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            tasks = []
            
            # Add company-specific API calls
            for company, config in companies.items():
                ats = config.get('ats', '').lower()
                slug = config.get('slug', '')
                
                if ats == 'greenhouse' and slug:
                    tasks.append(greenhouse.fetch(client, slug))
                elif ats == 'lever' and slug:
                    tasks.append(lever.fetch(client, slug))
                elif ats == 'ashby' and slug:
                    tasks.append(ashby.fetch(client, slug))
                elif ats == 'smartrecruiters' and slug:
                    tasks.append(smartrecruiters.fetch(client, slug))
            
            # Add general job board APIs
            tasks.extend([
                adzuna.search(client, location),
                greenhouse.fetch_public(client),
                lever.fetch_public(client)
            ])
            
            logger.info(f"Fetching jobs from {len(tasks)} sources...")
            batches = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect valid jobs from all sources
        all_jobs = []
        for i, batch in enumerate(batches):
            if isinstance(batch, list):
                all_jobs.extend(batch)
            elif isinstance(batch, Exception):
                logger.warning(f"Source {i} failed: {batch}")
        
        # Filter for currently open jobs
        open_jobs = [job for job in all_jobs if job.get("open", True)]
        logger.info(f"Found {len(open_jobs)} open jobs from {len(all_jobs)} total")
        
        # Validate links in parallel
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            validation_tasks = [head_ok(client, job["apply_url"]) for job in open_jobs]
            validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Keep only jobs with valid links
        valid_jobs = []
        for job, is_valid in zip(open_jobs, validation_results):
            if isinstance(is_valid, bool) and is_valid:
                valid_jobs.append(job)
            else:
                logger.debug(f"Dropping job {job.get('title', 'Unknown')} - invalid link")
        
        logger.info(f"Validated {len(valid_jobs)} jobs with working links")
        
        # Remove duplicates
        unique_jobs = dedupe_jobs(valid_jobs)
        logger.info(f"After deduplication: {len(unique_jobs)} unique jobs")
        
        # Rank jobs by relevance to resume
        if resume_text and unique_jobs:
            try:
                resume_vector = embed_resume(resume_text)
                jobs_with_vectors = embed_jobs(unique_jobs)
                ranked_jobs = rank(resume_vector, jobs_with_vectors)
                final_jobs = ranked_jobs[:max_jobs]
            except Exception as e:
                logger.warning(f"Ranking failed, using unranked results: {e}")
                final_jobs = unique_jobs[:max_jobs]
        else:
            final_jobs = unique_jobs[:max_jobs]
        
        # Calculate timing metrics
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log metrics
        logger.info(f"Live job search completed in {duration:.2f}s: "
                   f"{len(final_jobs)} jobs returned from {len(valid_jobs)} valid, "
                   f"{len(open_jobs)} open, {len(all_jobs)} total")
        
        return {
            "jobs": final_jobs,
            "metadata": {
                "total_fetched": len(all_jobs),
                "open_jobs": len(open_jobs),
                "valid_links": len(valid_jobs),
                "unique_jobs": len(unique_jobs),
                "returned": len(final_jobs),
                "duration_seconds": round(duration, 2),
                "sources_queried": len(tasks),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Live job search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

@router.get("/api/v1/jobs/live/health")
async def live_jobs_health():
    """Health check for live job search service"""
    try:
        # Test one source to verify connectivity
        async with httpx.AsyncClient(timeout=5) as client:
            test_jobs = await adzuna.search(client, "US", limit=1)
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "test_source": "adzuna",
                "test_result": len(test_jobs) >= 0
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@router.post("/api/v1/jobs/live/prewarm")
async def prewarm_jobs(background_tasks: BackgroundTasks):
    """
    Pre-warm job vectors for faster subsequent requests.
    Runs in background to avoid blocking the main endpoint.
    """
    background_tasks.add_task(_prewarm_job_vectors)
    return {"message": "Pre-warming job vectors in background"}

async def _prewarm_job_vectors():
    """Background task to pre-fetch and cache job vectors"""
    try:
        logger.info("Starting job vector pre-warming...")
        
        # Fetch fresh jobs from all sources
        async with httpx.AsyncClient(timeout=30) as client:
            tasks = [
                adzuna.search(client, "US", limit=100),
                greenhouse.fetch_public(client, limit=100),
                lever.fetch_public(client, limit=100)
            ]
            batches = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process and cache vectors
        all_jobs = []
        for batch in batches:
            if isinstance(batch, list):
                all_jobs.extend(batch)
        
        if all_jobs:
            # Embed and cache job vectors
            embed_jobs(all_jobs, cache=True)
            logger.info(f"Pre-warmed vectors for {len(all_jobs)} jobs")
        
    except Exception as e:
        logger.error(f"Pre-warming failed: {e}")
