from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Job Finder Service - Working Test",
    description="Live job matching service with mock data for testing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LiveJobSearchRequest(BaseModel):
    resume_text: str
    location: Optional[str] = "US"
    max_jobs: Optional[int] = 20
    timeout: Optional[int] = 12

class LiveJobSearchResponse(BaseModel):
    jobs: List[Dict]
    metadata: Dict

# Mock job data for testing
MOCK_JOBS = [
    {
        "id": "google_intern_001",
        "title": "Software Engineering Intern",
        "company": "Google",
        "description": "Join Google's engineering team as an intern! Work on real projects using Python, JavaScript, and cloud technologies.",
        "location": "Mountain View, CA",
        "apply_url": "https://careers.google.com/jobs/results/internships/123456",
        "posted_at": datetime.now().isoformat(),
        "open": True,
        "source": "greenhouse",
        "job_type": "Internship",
        "remote": "Hybrid",
        "salary_min": 8000,
        "salary_max": 12000,
        "duration": "12 weeks",
        "skills_required": ["Python", "JavaScript", "React", "Git", "Basic Algorithms"],
        "requirements": ["Currently enrolled in Computer Science", "GPA 3.0+", "Available for Summer 2024"],
        "match_score": 0.85,
        "matching_skills": ["Python", "JavaScript", "React"]
    },
    {
        "id": "microsoft_intern_002",
        "title": "Full Stack Development Intern",
        "company": "Microsoft",
        "description": "Build next-generation cloud applications using Azure, React, and TypeScript.",
        "location": "Seattle, WA",
        "apply_url": "https://careers.microsoft.com/us/en/job/internships/123456",
        "posted_at": datetime.now().isoformat(),
        "open": True,
        "source": "greenhouse",
        "job_type": "Internship",
        "remote": "Remote",
        "salary_min": 7500,
        "salary_max": 11000,
        "duration": "10 weeks",
        "skills_required": ["Python", "JavaScript", "React", "Azure", "TypeScript"],
        "requirements": ["Pursuing BS/MS in Computer Science", "Web development experience"],
        "match_score": 0.75,
        "matching_skills": ["Python", "JavaScript", "React"]
    },
    {
        "id": "amazon_intern_003",
        "title": "Backend Engineering Intern",
        "company": "Amazon",
        "description": "Design and implement scalable backend services using AWS, Python, and PostgreSQL.",
        "location": "Seattle, WA",
        "apply_url": "https://www.amazon.jobs/en/jobs/internships/123456",
        "posted_at": datetime.now().isoformat(),
        "open": True,
        "source": "greenhouse",
        "job_type": "Internship",
        "remote": "On-site",
        "salary_min": 8500,
        "salary_max": 13000,
        "duration": "12 weeks",
        "skills_required": ["Python", "Java", "AWS", "Docker", "PostgreSQL"],
        "requirements": ["Computer Science major", "Knowledge of data structures"],
        "match_score": 0.65,
        "matching_skills": ["Python"]
    }
]

@app.get("/")
async def root():
    return {"message": "Job Finder Service - Working Test Version", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "job-finder-working"}

@app.get("/api/v1/jobs/live/health")
async def live_jobs_health():
    """Health check for live job search service"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "companies_configured": 25,
        "sources_available": ["greenhouse", "lever", "ashby"],
        "mock_mode": True
    }

@app.post("/api/v1/jobs/live", response_model=LiveJobSearchResponse)
async def jobs_live(request: LiveJobSearchRequest):
    """
    Live job search endpoint with mock data for testing
    """
    start_time = datetime.now()
    
    try:
        # Simulate API delay
        await asyncio.sleep(1)
        
        # Filter jobs based on resume text
        resume_lower = request.resume_text.lower()
        filtered_jobs = []
        
        for job in MOCK_JOBS:
            # Simple keyword matching
            job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            score = 0
            
            # Check for skill matches
            for skill in job.get('skills_required', []):
                if skill.lower() in resume_lower:
                    score += 0.2
            
            # Check for keyword matches
            keywords = ['python', 'javascript', 'react', 'internship', 'intern']
            for keyword in keywords:
                if keyword in resume_lower and keyword in job_text:
                    score += 0.1
            
            job['match_score'] = min(score, 1.0)
            job['matching_skills'] = [skill for skill in job.get('skills_required', []) 
                                    if skill.lower() in resume_lower]
            
            filtered_jobs.append(job)
        
        # Sort by match score and limit results
        ranked_jobs = sorted(filtered_jobs, key=lambda x: x.get('match_score', 0.0), reverse=True)
        final_jobs = ranked_jobs[:request.max_jobs]
        
        # Calculate timing
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Mock live job search completed in {duration:.2f}s: {len(final_jobs)} jobs returned")
        
        return LiveJobSearchResponse(
            jobs=final_jobs,
            metadata={
                "total_fetched": len(MOCK_JOBS),
                "open_jobs": len(MOCK_JOBS),
                "valid_links": len(final_jobs),
                "unique_jobs": len(final_jobs),
                "returned": len(final_jobs),
                "duration_seconds": round(duration, 2),
                "sources_queried": 3,
                "timestamp": datetime.now().isoformat(),
                "checked_just_now": True,
                "mock_mode": True
            }
        )
        
    except Exception as e:
        logger.error(f"Mock live job search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
