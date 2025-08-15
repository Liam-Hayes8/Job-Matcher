import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from app.core.config import settings
from app.models import ATSJob, JobType

logger = logging.getLogger(__name__)

class ATSService:
    def __init__(self):
        self.available_services = []
        self.api_keys = {}
        
    async def initialize(self):
        """Initialize the ATS service with available API keys"""
        try:
            # Check which ATS APIs are available
            if settings.greenhouse_api_key:
                self.available_services.append("greenhouse")
                self.api_keys["greenhouse"] = settings.greenhouse_api_key
                
            if settings.lever_api_key:
                self.available_services.append("lever")
                self.api_keys["lever"] = settings.lever_api_key
                
            if settings.ashby_api_key:
                self.available_services.append("ashby")
                self.api_keys["ashby"] = settings.ashby_api_key
                
            if settings.smartrecruiters_api_key:
                self.available_services.append("smartrecruiters")
                self.api_keys["smartrecruiters"] = settings.smartrecruiters_api_key
                
            if settings.adzuna_app_id and settings.adzuna_app_key:
                self.available_services.append("adzuna")
                self.api_keys["adzuna"] = {
                    "app_id": settings.adzuna_app_id,
                    "app_key": settings.adzuna_app_key
                }
            
            logger.info(f"ATS Service initialized with services: {self.available_services}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ATS service: {e}")
    
    async def fetch_live_jobs(
        self, 
        client: httpx.AsyncClient,
        location: str = "US",
        days: int = 1,
        keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch live jobs from all available ATS APIs"""
        try:
            all_jobs = []
            
            # Fetch jobs from each ATS service concurrently
            tasks = []
            
            if "greenhouse" in self.available_services:
                tasks.append(self._fetch_greenhouse_jobs(client, location, days, keywords))
                
            if "lever" in self.available_services:
                tasks.append(self._fetch_lever_jobs(client, location, days, keywords))
                
            if "ashby" in self.available_services:
                tasks.append(self._fetch_ashby_jobs(client, location, days, keywords))
                
            if "smartrecruiters" in self.available_services:
                tasks.append(self._fetch_smartrecruiters_jobs(client, location, days, keywords))
                
            if "adzuna" in self.available_services:
                tasks.append(self._fetch_adzuna_jobs(client, location, days, keywords))
            
            # Execute all tasks concurrently
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        all_jobs.extend(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Error fetching jobs: {result}")
            
            # Filter for recent jobs
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_jobs = [
                job for job in all_jobs 
                if job.get("posted_at") and job["posted_at"] >= cutoff_date
            ]
            
            logger.info(f"Fetched {len(recent_jobs)} recent jobs from {len(self.available_services)} ATS services")
            return recent_jobs
            
        except Exception as e:
            logger.error(f"Error fetching live jobs: {e}")
            return []
    
    async def _fetch_greenhouse_jobs(
        self, 
        client: httpx.AsyncClient,
        location: str,
        days: int,
        keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from Greenhouse API"""
        try:
            jobs = []
            api_key = self.api_keys["greenhouse"]
            
            for company in settings.target_companies:
                try:
                    # Greenhouse Job Board API
                    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
                    headers = {"Authorization": f"Bearer {api_key}"}
                    
                    response = await client.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for job in data.get("jobs", []):
                        # Check if job is active and recent
                        if not job.get("active"):
                            continue
                            
                        posted_date = datetime.fromisoformat(job.get("updated_at", "").replace("Z", "+00:00"))
                        if posted_date < datetime.utcnow() - timedelta(days=days):
                            continue
                        
                        # Filter by location if specified
                        if location != "US" and location.lower() not in job.get("location", {}).get("name", "").lower():
                            continue
                        
                        jobs.append({
                            "id": f"greenhouse_{job['id']}",
                            "title": job.get("title", ""),
                            "company": company.title(),
                            "description": job.get("content", ""),
                            "location": job.get("location", {}).get("name", ""),
                            "apply_url": job.get("absolute_url", ""),
                            "posted_at": posted_date,
                            "ats_source": "greenhouse",
                            "raw_data": job
                        })
                        
                except Exception as e:
                    logger.warning(f"Error fetching Greenhouse jobs for {company}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error in Greenhouse job fetch: {e}")
            return []
    
    async def _fetch_lever_jobs(
        self, 
        client: httpx.AsyncClient,
        location: str,
        days: int,
        keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from Lever API"""
        try:
            jobs = []
            api_key = self.api_keys["lever"]
            
            for company in settings.target_companies:
                try:
                    # Lever Postings API
                    url = f"https://api.lever.co/v0/postings/{company}"
                    headers = {"Authorization": f"Bearer {api_key}"}
                    
                    response = await client.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for job in data:
                        # Check if job is active and recent
                        if not job.get("state") == "active":
                            continue
                            
                        posted_date = datetime.fromtimestamp(job.get("createdAt", 0) / 1000)
                        if posted_date < datetime.utcnow() - timedelta(days=days):
                            continue
                        
                        # Filter by location if specified
                        if location != "US" and location.lower() not in job.get("categories", {}).get("location", "").lower():
                            continue
                        
                        jobs.append({
                            "id": f"lever_{job['id']}",
                            "title": job.get("text", ""),
                            "company": company.title(),
                            "description": job.get("descriptionPlain", ""),
                            "location": job.get("categories", {}).get("location", ""),
                            "apply_url": job.get("hostedUrl", ""),
                            "posted_at": posted_date,
                            "ats_source": "lever",
                            "raw_data": job
                        })
                        
                except Exception as e:
                    logger.warning(f"Error fetching Lever jobs for {company}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error in Lever job fetch: {e}")
            return []
    
    async def _fetch_ashby_jobs(
        self, 
        client: httpx.AsyncClient,
        location: str,
        days: int,
        keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from Ashby API"""
        try:
            jobs = []
            api_key = self.api_keys["ashby"]
            
            for company in settings.target_companies:
                try:
                    # Ashby Job Postings API
                    url = f"https://api.ashbyhq.com/v1/job-posting/list"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "organizationId": company,
                        "limit": 100
                    }
                    
                    response = await client.post(url, headers=headers, json=payload, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for job in data.get("jobPostings", []):
                        # Check if job is active and recent
                        if not job.get("isActive"):
                            continue
                            
                        posted_date = datetime.fromisoformat(job.get("createdAt", "").replace("Z", "+00:00"))
                        if posted_date < datetime.utcnow() - timedelta(days=days):
                            continue
                        
                        jobs.append({
                            "id": f"ashby_{job['id']}",
                            "title": job.get("title", ""),
                            "company": company.title(),
                            "description": job.get("description", ""),
                            "location": job.get("location", ""),
                            "apply_url": job.get("applicationUrl", ""),
                            "posted_at": posted_date,
                            "ats_source": "ashby",
                            "raw_data": job
                        })
                        
                except Exception as e:
                    logger.warning(f"Error fetching Ashby jobs for {company}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error in Ashby job fetch: {e}")
            return []
    
    async def _fetch_smartrecruiters_jobs(
        self, 
        client: httpx.AsyncClient,
        location: str,
        days: int,
        keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from SmartRecruiters API"""
        try:
            jobs = []
            api_key = self.api_keys["smartrecruiters"]
            
            for company in settings.target_companies:
                try:
                    # SmartRecruiters Posting API
                    url = f"https://api.smartrecruiters.com/v1/companies/{company}/postings"
                    headers = {"X-SmartToken": api_key}
                    
                    response = await client.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for job in data.get("content", []):
                        # Check if job is active and recent
                        if not job.get("status") == "PUBLISHED":
                            continue
                            
                        posted_date = datetime.fromisoformat(job.get("createdAt", "").replace("Z", "+00:00"))
                        if posted_date < datetime.utcnow() - timedelta(days=days):
                            continue
                        
                        jobs.append({
                            "id": f"smartrecruiters_{job['id']}",
                            "title": job.get("name", ""),
                            "company": company.title(),
                            "description": job.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text", ""),
                            "location": job.get("location", {}).get("city", ""),
                            "apply_url": job.get("applyUrl", ""),
                            "posted_at": posted_date,
                            "ats_source": "smartrecruiters",
                            "raw_data": job
                        })
                        
                except Exception as e:
                    logger.warning(f"Error fetching SmartRecruiters jobs for {company}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error in SmartRecruiters job fetch: {e}")
            return []
    
    async def _fetch_adzuna_jobs(
        self, 
        client: httpx.AsyncClient,
        location: str,
        days: int,
        keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from Adzuna API (aggregator)"""
        try:
            jobs = []
            api_creds = self.api_keys["adzuna"]
            
            # Adzuna Job Search API
            url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
            params = {
                "app_id": api_creds["app_id"],
                "app_key": api_creds["app_key"],
                "results_per_page": 50,
                "what": " ".join(keywords) if keywords else "software engineer",
                "where": location if location != "US" else "san francisco",
                "days": days
            }
            
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for job in data.get("results", []):
                posted_date = datetime.fromisoformat(job.get("created", "").replace("Z", "+00:00"))
                
                jobs.append({
                    "id": f"adzuna_{job['id']}",
                    "title": job.get("title", ""),
                    "company": job.get("company", {}).get("display_name", ""),
                    "description": job.get("description", ""),
                    "location": job.get("location", {}).get("display_name", ""),
                    "apply_url": job.get("redirect_url", ""),
                    "posted_at": posted_date,
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "ats_source": "adzuna",
                    "raw_data": job
                })
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error in Adzuna job fetch: {e}")
            return []
    
    async def is_job_valid(self, client: httpx.AsyncClient, job: Dict[str, Any]) -> bool:
        """Check if a job posting is still valid by testing the apply URL"""
        try:
            apply_url = job.get("apply_url")
            if not apply_url:
                return False
            
            # Make a HEAD request to check if the URL is accessible
            response = await client.head(apply_url, timeout=5, follow_redirects=True)
            
            # Consider valid if status code is 2xx or 3xx
            return 200 <= response.status_code < 400
            
        except Exception as e:
            logger.debug(f"Error validating job URL {job.get('apply_url', '')}: {e}")
            return False
    
    def get_available_services(self) -> List[str]:
        """Get list of available ATS services"""
        return self.available_services.copy()
