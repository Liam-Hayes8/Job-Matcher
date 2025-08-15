from fastapi import APIRouter, HTTPException, BackgroundTasks
import asyncio
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import yaml
import os
import hashlib
import random

logger = logging.getLogger(__name__)
router = APIRouter()

# Mock job sources for local development
MOCK_JOBS = [
    {
        "id": "google_001",
        "title": "Senior Software Engineer",
        "company": "Google",
        "description": "Join Google's engineering team to build scalable systems. We're looking for engineers with experience in Python, JavaScript, and cloud technologies.",
        "location": "Mountain View, CA",
        "apply_url": "https://careers.google.com/jobs/results/123456",
        "posted_at": datetime.now().isoformat(),
        "open": True,
        "source": "greenhouse",
        "job_id": "001",
        "department": "Engineering",
        "job_type": "Full-time",
        "remote": "Hybrid",
        "salary_min": 150000,
        "salary_max": 250000,
        "skills_required": ["Python", "JavaScript", "React", "Go", "Kubernetes"]
    },
    {
        "id": "microsoft_002",
        "title": "Full Stack Developer",
        "company": "Microsoft",
        "description": "Build next-generation cloud applications using Azure, React, and TypeScript. Experience with cloud services and modern web development required.",
        "location": "Seattle, WA",
        "apply_url": "https://careers.microsoft.com/us/en/job/123456",
        "posted_at": datetime.now().isoformat(),
        "open": True,
        "source": "greenhouse",
        "job_id": "002",
        "department": "Cloud & AI",
        "job_type": "Full-time",
        "remote": "Remote",
        "salary_min": 120000,
        "salary_max": 200000,
        "skills_required": ["Python", "JavaScript", "React", "Azure", "TypeScript"]
    },
    {
        "id": "amazon_003",
        "title": "Backend Engineer",
        "company": "Amazon",
        "description": "Design and implement scalable backend services using AWS, Python, and PostgreSQL. Experience with microservices architecture preferred.",
        "location": "Seattle, WA",
        "apply_url": "https://www.amazon.jobs/en/jobs/123456",
        "posted_at": datetime.now().isoformat(),
        "open": True,
        "source": "greenhouse",
        "job_id": "003",
        "department": "AWS",
        "job_type": "Full-time",
        "remote": "On-site",
        "salary_min": 130000,
        "salary_max": 220000,
        "skills_required": ["Python", "Java", "AWS", "Docker", "PostgreSQL"]
    },
    {
        "id": "uber_004",
        "title": "Software Engineer - Platform",
        "company": "Uber",
        "description": "Build the platform that powers Uber's global operations. Work with Go, Python, and distributed systems.",
        "location": "San Francisco, CA",
        "apply_url": "https://www.uber.com/careers/list/123456",
        "posted_at": datetime.now().isoformat(),
        "open": True,
        "source": "lever",
        "job_id": "004",
        "department": "Platform",
        "job_type": "Full-time",
        "remote": "Hybrid",
        "salary_min": 140000,
        "salary_max": 230000,
        "skills_required": ["Go", "Python", "Distributed Systems", "Kubernetes"]
    },
    {
        "id": "stripe_005",
        "title": "Full Stack Engineer",
        "company": "Stripe",
        "description": "Build the future of online payments. Work with React, TypeScript, and Ruby on Rails.",
        "location": "San Francisco, CA",
        "apply_url": "https://stripe.com/jobs/123456",
        "posted_at": datetime.now().isoformat(),
        "open": True,
        "source": "lever",
        "job_id": "005",
        "department": "Payments",
        "job_type": "Full-time",
        "remote": "Remote",
        "salary_min": 130000,
        "salary_max": 210000,
        "skills_required": ["React", "TypeScript", "Ruby", "PostgreSQL"]
    }
]

async def mock_head_ok(client: httpx.AsyncClient, url: str) -> bool:
    """Mock URL validation - always returns True for local development"""
    return True

def mock_dedupe_jobs(jobs: List[Dict]) -> List[Dict]:
    """Remove duplicate jobs based on title, company, and location."""
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        key = hashlib.md5(
            f"{job.get('title', '')}{job.get('company', '')}{job.get('location', '')}".encode()
        ).hexdigest()
        
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    return unique_jobs

def mock_rank_jobs(resume_text: str, jobs: List[Dict]) -> List[Dict]:
    """Mock job ranking based on simple keyword matching."""
    if not resume_text or not jobs:
        return jobs
    
    # Simple keyword matching
    resume_lower = resume_text.lower()
    keywords = ["python", "javascript", "react", "aws", "docker", "postgresql", "fastapi"]
    
    for job in jobs:
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        score = 0
        
        for keyword in keywords:
            if keyword in resume_lower and keyword in job_text:
                score += 0.2
        
        # Add some randomness for variety
        score += random.uniform(0, 0.3)
        job["match_score"] = min(score, 1.0)
        job["matching_skills"] = [skill for skill in job.get("skills_required", []) 
                                if skill.lower() in resume_lower]
    
    # Sort by score
    return sorted(jobs, key=lambda x: x.get("match_score", 0.0), reverse=True)

@router.post("/api/v1/jobs/live")
async def jobs_live_local(
    resume_text: str, 
    location: str = "US",
    max_jobs: int = 50,
    timeout: int = 12
):
    """
    Mock live job search for local development.
    Simulates real-time job fetching with mock data.
    """
    start_time = datetime.now()
    
    try:
        # Simulate API delay
        await asyncio.sleep(1)
        
        # Get mock jobs
        all_jobs = MOCK_JOBS.copy()
        
        # Filter for open jobs
        open_jobs = [job for job in all_jobs if job.get("open", True)]
        
        # Simulate link validation
        async with httpx.AsyncClient(timeout=5) as client:
            validation_tasks = [mock_head_ok(client, job["apply_url"]) for job in open_jobs]
            validation_results = await asyncio.gather(*validation_tasks)
        
        # Keep jobs with valid links
        valid_jobs = [job for job, is_valid in zip(open_jobs, validation_results) if is_valid]
        
        # Remove duplicates
        unique_jobs = mock_dedupe_jobs(valid_jobs)
        
        # Rank jobs by relevance
        if resume_text and unique_jobs:
            ranked_jobs = mock_rank_jobs(resume_text, unique_jobs)
            final_jobs = ranked_jobs[:max_jobs]
        else:
            final_jobs = unique_jobs[:max_jobs]
        
        # Calculate timing
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Mock live job search completed in {duration:.2f}s: "
                   f"{len(final_jobs)} jobs returned")
        
        return {
            "jobs": final_jobs,
            "metadata": {
                "total_fetched": len(all_jobs),
                "open_jobs": len(open_jobs),
                "valid_links": len(valid_jobs),
                "unique_jobs": len(unique_jobs),
                "returned": len(final_jobs),
                "duration_seconds": round(duration, 2),
                "sources_queried": 3,  # Mock sources
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Mock live job search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

@router.get("/api/v1/jobs/live/health")
async def live_jobs_health_local():
    """Health check for mock live job search service"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "test_source": "mock",
        "test_result": True
    }

@router.post("/api/v1/jobs/live/prewarm")
async def prewarm_jobs_local(background_tasks: BackgroundTasks):
    """Mock pre-warming for local development"""
    background_tasks.add_task(_mock_prewarm_job_vectors)
    return {"message": "Mock pre-warming job vectors in background"}

async def _mock_prewarm_job_vectors():
    """Mock background task to pre-fetch and cache job vectors"""
    try:
        logger.info("Starting mock job vector pre-warming...")
        await asyncio.sleep(2)  # Simulate processing time
        logger.info("Mock pre-warmed vectors for jobs")
    except Exception as e:
        logger.error(f"Mock pre-warming failed: {e}")
