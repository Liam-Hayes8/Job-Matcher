import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

async def fetch(client: httpx.AsyncClient, company_slug: str, limit: int = 50) -> List[Dict]:
    """
    Fetch jobs from SmartRecruiters API for a specific company.
    Uses the public postings API which returns currently published jobs.
    """
    try:
        url = f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings"
        params = {
            "limit": limit,
            "status": "published"
        }
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        jobs = data.get("content", [])
        
        normalized_jobs = []
        for job in jobs:
            try:
                normalized_job = {
                    "title": job.get("name", ""),
                    "company": company_slug.title(),
                    "description": job.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text", ""),
                    "location": job.get("location", {}).get("city", ""),
                    "apply_url": job.get("applyUrl", ""),
                    "posted_at": job.get("releasedDate", ""),
                    "open": job.get("status", "") == "published",
                    "source": "smartrecruiters",
                    "job_id": job.get("id", ""),
                    "department": job.get("department", {}).get("label", ""),
                    "job_type": _extract_job_type(job.get("name", "")),
                    "remote": _extract_remote_status(job.get("name", "") + " " + job.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text", ""))
                }
                
                if normalized_job["apply_url"] and normalized_job["open"]:
                    normalized_jobs.append(normalized_job)
                    
            except Exception as e:
                logger.warning(f"Failed to normalize SmartRecruiters job {job.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Fetched {len(normalized_jobs)} jobs from SmartRecruiters ({company_slug})")
        return normalized_jobs
        
    except Exception as e:
        logger.error(f"SmartRecruiters API error for {company_slug}: {e}")
        return []

def _extract_job_type(title: str) -> str:
    """Extract job type from title"""
    title_lower = title.lower()
    if any(word in title_lower for word in ["intern", "internship"]):
        return "Internship"
    elif any(word in title_lower for word in ["contract", "freelance"]):
        return "Contract"
    elif any(word in title_lower for word in ["part-time", "parttime"]):
        return "Part-time"
    else:
        return "Full-time"

def _extract_remote_status(text: str) -> str:
    """Extract remote status from text"""
    text_lower = text.lower()
    if any(word in text_lower for word in ["remote", "work from home", "wfh"]):
        return "Remote"
    elif any(word in text_lower for word in ["hybrid", "flexible"]):
        return "Hybrid"
    else:
        return "On-site"
