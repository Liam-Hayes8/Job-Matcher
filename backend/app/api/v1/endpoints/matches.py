from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.resume import Resume, JobListing, JobMatch
from app.schemas.resume import JobMatchResponse
from app.services.resume_service import resume_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{resume_id}", response_model=List[JobMatchResponse])
async def find_job_matches(
    resume_id: int,
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    if not hasattr(request.state, 'user_id') or not request.state.user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = request.state.user_id
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not resume.parsed_data:
        raise HTTPException(status_code=400, detail="Resume must be parsed before finding matches")
    
    try:
        job_listings = db.query(JobListing).all()
        
        job_data = []
        for job in job_listings:
            job_data.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "requirements": job.requirements or "",
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "job_type": job.job_type,
                "remote": job.remote
            })
        
        matches = resume_service.get_matching_jobs(resume.parsed_data, job_data)
        
        db.query(JobMatch).filter(JobMatch.resume_id == resume_id).delete()
        
        results = []
        for match in matches[:limit]:
            db_match = JobMatch(
                resume_id=resume_id,
                job_listing_id=match["id"],
                match_score=match["match_score"],
                matching_skills=match["matching_skills"]
            )
            db.add(db_match)
            
            job_listing = db.query(JobListing).filter(JobListing.id == match["id"]).first()
            results.append(JobMatchResponse(
                job_listing=job_listing,
                match_score=match["match_score"],
                matching_skills=match["matching_skills"]
            ))
        
        db.commit()
        return results
        
    except Exception as e:
        logger.error(f"Failed to find job matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to find job matches")

@router.get("/{resume_id}", response_model=List[JobMatchResponse])
async def get_job_matches(
    resume_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    if not hasattr(request.state, 'user_id') or not request.state.user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = request.state.user_id
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    matches = db.query(JobMatch).filter(JobMatch.resume_id == resume_id).all()
    
    results = []
    for match in matches:
        results.append(JobMatchResponse(
            job_listing=match.job_listing,
            match_score=match.match_score,
            matching_skills=match.matching_skills or []
        ))
    
    return results