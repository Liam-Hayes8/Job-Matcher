from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json

class ResumeBase(BaseModel):
    filename: str
    content: Optional[str] = None

class ResumeCreate(ResumeBase):
    user_id: str

class ResumeUpdate(BaseModel):
    content: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None

class Resume(ResumeBase):
    id: int
    user_id: str
    file_path: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobListingBase(BaseModel):
    title: str
    company: str
    description: str
    requirements: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[str] = None
    remote: Optional[str] = None

class JobListingCreate(JobListingBase):
    pass

class JobListing(JobListingBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobMatchBase(BaseModel):
    match_score: float
    matching_skills: Optional[List[str]] = None

class JobMatch(JobMatchBase):
    id: int
    resume_id: int
    job_listing_id: int
    created_at: datetime
    job_listing: JobListing

    class Config:
        from_attributes = True

class JobMatchResponse(BaseModel):
    job_listing: JobListing
    match_score: float
    matching_skills: List[str]

class ResumeParseResponse(BaseModel):
    skills: List[str]
    experience: List[Dict[str, Any]]
    contact_info: Dict[str, str]