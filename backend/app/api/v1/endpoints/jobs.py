from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.resume import JobListing
from app.schemas.resume import JobListing as JobListingSchema, JobListingCreate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=JobListingSchema)
async def create_job_listing(
    job_data: JobListingCreate,
    db: Session = Depends(get_db)
):
    try:
        db_job = JobListing(**job_data.dict())
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    except Exception as e:
        logger.error(f"Failed to create job listing: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job listing")

@router.get("/", response_model=List[JobListingSchema])
async def get_job_listings(
    skip: int = 0,
    limit: int = 100,
    company: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    remote: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(JobListing)
    
    if company:
        query = query.filter(JobListing.company.ilike(f"%{company}%"))
    if location:
        query = query.filter(JobListing.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(JobListing.job_type == job_type)
    if remote:
        query = query.filter(JobListing.remote == remote)
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=JobListingSchema)
async def get_job_listing(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found")
    return job

@router.put("/{job_id}", response_model=JobListingSchema)
async def update_job_listing(
    job_id: int,
    job_data: JobListingCreate,
    db: Session = Depends(get_db)
):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found")
    
    try:
        for field, value in job_data.dict().items():
            setattr(job, field, value)
        
        db.commit()
        db.refresh(job)
        return job
    except Exception as e:
        logger.error(f"Failed to update job listing: {e}")
        raise HTTPException(status_code=500, detail="Failed to update job listing")

@router.delete("/{job_id}")
async def delete_job_listing(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found")
    
    try:
        db.delete(job)
        db.commit()
        return {"message": "Job listing deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete job listing: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete job listing")