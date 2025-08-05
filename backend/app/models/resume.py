from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content = Column(Text)
    parsed_data = Column(JSON)11
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    job_matches = relationship("JobMatch", back_populates="resume")

class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    location = Column(String)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    job_type = Column(String)
    remote = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    job_matches = relationship("JobMatch", back_populates="job_listing")

class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_listing_id = Column(Integer, ForeignKey("job_listings.id"), nullable=False)
    match_score = Column(Float, nullable=False)
    matching_skills = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="job_matches")
    job_listing = relationship("JobListing", back_populates="job_matches")