import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

async def fetch(client: httpx.AsyncClient, company_slug: str, limit: int = 50) -> List[Dict]:
    """
    Fetch jobs from Greenhouse API for a specific company.
    Uses the public job board API which returns currently published jobs.
    """
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
        response = await client.get(url)
        response.raise_for_status()
        
        data = response.json()
        jobs = data.get("jobs", [])
        
        normalized_jobs = []
        for job in jobs[:limit]:
            try:
                normalized_job = {
                    "title": job.get("title", ""),
                    "company": job.get("location", {}).get("name", company_slug.title()),
                    "description": job.get("content", ""),
                    "location": job.get("location", {}).get("name", ""),
                    "apply_url": job.get("absolute_url", ""),
                    "posted_at": job.get("updated_at", ""),
                    "open": job.get("status", "") == "open",
                    "source": "greenhouse",
                    "job_id": job.get("id", ""),
                    "department": job.get("departments", [{}])[0].get("name", "") if job.get("departments") else "",
                    "job_type": _extract_job_type(job.get("title", "")),
                    "remote": _extract_remote_status(job.get("title", "") + " " + job.get("content", ""))
                }
                
                if normalized_job["apply_url"] and normalized_job["open"]:
                    normalized_jobs.append(normalized_job)
                    
            except Exception as e:
                logger.warning(f"Failed to normalize Greenhouse job {job.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Fetched {len(normalized_jobs)} jobs from Greenhouse ({company_slug})")
        return normalized_jobs
        
    except Exception as e:
        logger.error(f"Greenhouse API error for {company_slug}: {e}")
        return []

async def fetch_public(client: httpx.AsyncClient, limit: int = 50) -> List[Dict]:
    """
    Fetch jobs from public Greenhouse job boards.
    This is a fallback for companies not in our curated list.
    """
    # Greenhouse doesn't have a public search API, so we'll return empty
    # In production, you might maintain a list of public Greenhouse boards
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
