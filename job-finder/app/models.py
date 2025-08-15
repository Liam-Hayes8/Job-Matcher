from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"

class JobRequest(BaseModel):
    resume_text: str = Field(..., description="Resume text content")
    location: str = Field(default="US", description="Job location (country or city)")
    days: int = Field(default=1, description="Number of days back to search")
    keywords: Optional[List[str]] = Field(default=None, description="Optional keywords to filter jobs")
    limit: int = Field(default=20, description="Maximum number of jobs to return")
    min_salary: Optional[int] = Field(default=None, description="Minimum salary requirement")
    max_salary: Optional[int] = Field(default=None, description="Maximum salary requirement")
    job_types: Optional[List[JobType]] = Field(default=None, description="Preferred job types")
    remote_only: bool = Field(default=False, description="Only remote jobs")

class JobResponse(BaseModel):
    id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    location: str = Field(..., description="Job location")
    apply_url: str = Field(..., description="Direct apply URL")
    posted_at: datetime = Field(..., description="When the job was posted")
    match_score: float = Field(..., description="Similarity score (0-1)")
    matching_skills: List[str] = Field(default=[], description="Skills that match the resume")
    salary_min: Optional[int] = Field(default=None, description="Minimum salary")
    salary_max: Optional[int] = Field(default=None, description="Maximum salary")
    job_type: Optional[JobType] = Field(default=None, description="Job type")
    remote: bool = Field(default=False, description="Whether the job is remote")
    ats_source: str = Field(..., description="Source ATS system")
    requirements: Optional[str] = Field(default=None, description="Job requirements")
    benefits: Optional[str] = Field(default=None, description="Job benefits")

class JobMatch(BaseModel):
    job: JobResponse
    score: float
    skills_match: List[str]
    experience_match: float

class ATSJob(BaseModel):
    """Internal representation of a job from ATS APIs"""
    id: str
    title: str
    company: str
    description: str
    location: str
    apply_url: str
    posted_at: datetime
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[JobType] = None
    remote: bool = False
    ats_source: str
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class CachedJob(BaseModel):
    """Job stored in cache with embedding"""
    id: str
    title: str
    company: str
    description: str
    location: str
    apply_url: str
    posted_at: datetime
    embedding: List[float]
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[JobType] = None
    remote: bool = False
    ats_source: str
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    cached_at: datetime
    last_verified: datetime

class ServiceStats(BaseModel):
    total_jobs_cached: int
    ats_services_available: List[str]
    embedding_model: str
    last_cache_refresh: Optional[datetime]
    average_response_time: float
    cache_hit_rate: float
