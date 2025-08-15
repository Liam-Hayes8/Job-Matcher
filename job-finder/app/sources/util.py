import httpx
import logging
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def head_ok(client: httpx.AsyncClient, url: str) -> bool:
    """
    Validate that a job apply URL is still active.
    Returns True if the URL is valid and the job is still available.
    """
    try:
        # Try HEAD first (more efficient)
        response = await client.head(url, follow_redirects=True, timeout=8)
        
        # If HEAD is not allowed, try GET
        if response.status_code == 405:
            response = await client.get(url, follow_redirects=True, timeout=8)
        
        # Check if status code indicates success
        if response.status_code // 100 != 2:
            logger.debug(f"URL {url} returned status {response.status_code}")
            return False
        
        # Quick body sniff to catch "no longer available" messages
        if response.text:
            snippet = response.text[:2000].lower()
            if any(phrase in snippet for phrase in [
                "no longer available",
                "job not found", 
                "position closed",
                "this position has been filled",
                "application closed",
                "no longer accepting applications"
            ]):
                logger.debug(f"URL {url} contains 'no longer available' message")
                return False
        
        return True
        
    except Exception as e:
        logger.debug(f"Error validating URL {url}: {e}")
        return False

def dedupe_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Remove duplicate jobs based on company, title, and location.
    Prefer the newest job when duplicates are found.
    """
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        # Create a unique key based on company, title, and location
        key = hashlib.md5(
            f"{job.get('company', '')}{job.get('title', '')}{job.get('location', '')}".encode()
        ).hexdigest()
        
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
        else:
            # If we have a duplicate, keep the newer one
            existing_job = next(j for j in unique_jobs if hashlib.md5(
                f"{j.get('company', '')}{j.get('title', '')}{j.get('location', '')}".encode()
            ).hexdigest() == key)
            
            # Compare posted dates
            existing_date = existing_job.get('posted_at', '')
            new_date = job.get('posted_at', '')
            
            if new_date > existing_date:
                # Replace the existing job with the newer one
                unique_jobs.remove(existing_job)
                unique_jobs.append(job)
    
    return unique_jobs

def filter_recent_jobs(jobs: List[Dict], max_age_hours: int = 48) -> List[Dict]:
    """
    Filter jobs to only include those posted within the last max_age_hours.
    """
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    recent_jobs = []
    
    for job in jobs:
        try:
            posted_at = datetime.fromisoformat(job.get('posted_at', '').replace('Z', '+00:00'))
            if posted_at >= cutoff_time:
                recent_jobs.append(job)
        except (ValueError, TypeError):
            # If we can't parse the date, include the job (better safe than sorry)
            recent_jobs.append(job)
    
    return recent_jobs

def rank_jobs_by_relevance(jobs: List[Dict], resume_text: str) -> List[Dict]:
    """
    Rank jobs by relevance to the resume text.
    This is a simple keyword-based ranking - can be enhanced with embeddings later.
    """
    if not resume_text or not jobs:
        return jobs
    
    resume_lower = resume_text.lower()
    
    for job in jobs:
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        score = 0
        
        # Check for skill matches
        skills = job.get('skills_required', [])
        for skill in skills:
            if skill.lower() in resume_lower:
                score += 0.2
        
        # Check for keyword matches
        keywords = [
            'python', 'javascript', 'react', 'aws', 'docker', 'postgresql', 
            'fastapi', 'swift', 'machine learning', 'data science', 
            'product management', 'internship', 'intern'
        ]
        
        for keyword in keywords:
            if keyword in resume_lower and keyword in job_text:
                score += 0.1
        
        # Bonus for internship matches if resume mentions student/internship
        if 'intern' in job_text and any(word in resume_lower for word in ['student', 'intern', 'internship']):
            score += 0.3
        
        job['match_score'] = min(score, 1.0)
    
    # Sort by score (highest first)
    return sorted(jobs, key=lambda x: x.get('match_score', 0.0), reverse=True)

async def fetch_all_live(companies: List[Dict], client: httpx.AsyncClient) -> List[Dict]:
    """
    Fetch jobs from all configured ATS sources concurrently.
    """
    import asyncio
    from . import greenhouse, lever, ashby
    
    # Create tasks for each ATS source
    tasks = [
        greenhouse.fetch(client, companies),
        lever.fetch(client, companies),
        ashby.fetch(client, companies)
    ]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results, filtering out exceptions
    all_jobs = []
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)
        else:
            logger.error(f"Error fetching jobs: {result}")
    
    return all_jobs

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skills from resume text.
    """
    skills = []
    text_lower = text.lower()
    
    # Common tech skills
    tech_skills = [
        'python', 'javascript', 'react', 'node.js', 'java', 'c++', 'c#', 'go', 'rust',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'postgresql', 'mysql', 'mongodb',
        'machine learning', 'ai', 'data science', 'sql', 'html', 'css', 'typescript',
        'swift', 'kotlin', 'android', 'ios', 'flutter', 'react native', 'fastapi',
        'django', 'flask', 'express', 'spring', 'angular', 'vue', 'svelte'
    ]
    
    for skill in tech_skills:
        if skill in text_lower:
            skills.append(skill.title())
    
    return skills
