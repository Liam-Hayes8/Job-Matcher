import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Adzuna API credentials (should be in environment variables)
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY", "")

async def search(client: httpx.AsyncClient, location: str = "US", limit: int = 50) -> List[Dict]:
    """
    Search jobs from Adzuna API.
    Returns jobs from today with canonical redirect URLs.
    """
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        logger.warning("Adzuna API credentials not configured")
        return []
    
    try:
        # Map location to Adzuna country codes
        country_map = {
            "US": "us",
            "GB": "gb", 
            "AU": "au",
            "BR": "br",
            "CA": "ca",
            "DE": "de",
            "FR": "fr",
            "IN": "in",
            "IT": "it",
            "MX": "mx",
            "NL": "nl",
            "NZ": "nz",
            "PL": "pl",
            "RU": "ru",
            "SG": "sg",
            "ES": "es",
            "SE": "se",
            "ZA": "za"
        }
        
        country = country_map.get(location.upper(), "us")
        
        # Search for jobs from today
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_API_KEY,
            "results_per_page": min(limit, 50),
            "what": "software engineer developer python javascript",
            "content-type": "application/json"
        }
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        jobs = data.get("results", [])
        
        normalized_jobs = []
        for job in jobs:
            try:
                normalized_job = {
                    "title": job.get("title", ""),
                    "company": job.get("company", {}).get("display_name", ""),
                    "description": job.get("description", ""),
                    "location": job.get("location", {}).get("display_name", ""),
                    "apply_url": job.get("redirect_url", ""),
                    "posted_at": job.get("created", ""),
                    "open": True,  # Adzuna only returns active jobs
                    "source": "adzuna",
                    "job_id": job.get("id", ""),
                    "salary_min": _extract_salary(job.get("salary_min")),
                    "salary_max": _extract_salary(job.get("salary_max")),
                    "job_type": _extract_job_type(job.get("title", "")),
                    "remote": _extract_remote_status(job.get("title", "") + " " + job.get("description", ""))
                }
                
                if normalized_job["apply_url"]:
                    normalized_jobs.append(normalized_job)
                    
            except Exception as e:
                logger.warning(f"Failed to normalize Adzuna job {job.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Fetched {len(normalized_jobs)} jobs from Adzuna ({country})")
        return normalized_jobs
        
    except Exception as e:
        logger.error(f"Adzuna API error: {e}")
        return []

def _extract_salary(salary_value) -> Optional[int]:
    """Extract salary value"""
    if salary_value and isinstance(salary_value, (int, float)):
        return int(salary_value)
    return None

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
