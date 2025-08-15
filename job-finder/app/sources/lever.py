import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def fetch(client: httpx.AsyncClient, companies: List[Dict]) -> List[Dict]:
    """
    Fetch jobs from Lever API for specified companies.
    Returns jobs with canonical apply URLs.
    """
    jobs = []
    
    for company in companies:
        if company.get('ats') != 'lever':
            continue
            
        site_handle = company.get('slug')
        if not site_handle:
            logger.warning(f"No site handle for company {company.get('name')}")
            continue
            
        try:
            # Lever Postings API
            url = f"https://api.lever.co/v0/postings/{site_handle}"
            
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for job in data:
                # Only include jobs that are currently open
                if not job.get('state', '') == 'published':
                    continue
                    
                # Get the canonical apply URL (prefer hostedUrl, fallback to applyUrl)
                apply_url = job.get('hostedUrl') or job.get('applyUrl')
                if not apply_url:
                    continue
                
                # Parse location
                location = job.get('categories', {}).get('location', 'Remote')
                
                # Parse job type and remote status
                job_type = _extract_job_type(job)
                remote_status = _extract_remote_status(job)
                
                # Parse salary if available
                salary_min, salary_max = _extract_salary(job)
                
                # Extract skills from job description
                skills_required = _extract_skills(job.get('text', ''))
                
                jobs.append({
                    'id': f"lever_{job['id']}",
                    'title': job.get('text', ''),
                    'company': company.get('name', ''),
                    'description': job.get('descriptionPlain', ''),
                    'location': location,
                    'apply_url': apply_url,
                    'posted_at': job.get('createdAt', datetime.now().isoformat()),
                    'open': True,
                    'source': 'lever',
                    'job_id': job['id'],
                    'department': job.get('categories', {}).get('department', ''),
                    'job_type': job_type,
                    'remote': remote_status,
                    'salary_min': salary_min,
                    'salary_max': salary_max,
                    'skills_required': skills_required,
                    'requirements': _extract_requirements(job.get('descriptionPlain', ''))
                })
                
        except Exception as e:
            logger.error(f"Error fetching from Lever for {company.get('name')}: {e}")
            continue
    
    return jobs

def _extract_job_type(job: Dict) -> str:
    """Extract job type from Lever job data"""
    # Check for internship indicators
    title = job.get('text', '').lower()
    description = job.get('descriptionPlain', '').lower()
    
    if any(word in title for word in ['intern', 'internship', 'co-op']):
        return 'Internship'
    elif any(word in description for word in ['intern', 'internship', 'co-op']):
        return 'Internship'
    else:
        return 'Full-time'

def _extract_remote_status(job: Dict) -> str:
    """Extract remote status from Lever job data"""
    location = job.get('categories', {}).get('location', '').lower()
    description = job.get('descriptionPlain', '').lower()
    
    if 'remote' in location or 'remote' in description:
        return 'Remote'
    elif 'hybrid' in description:
        return 'Hybrid'
    else:
        return 'On-site'

def _extract_salary(job: Dict) -> tuple[Optional[int], Optional[int]]:
    """Extract salary range from Lever job data"""
    # Lever doesn't always expose salary in the API
    # This would need to be enhanced with additional parsing
    return None, None

def _extract_skills(content: str) -> List[str]:
    """Extract required skills from job content"""
    skills = []
    content_lower = content.lower()
    
    # Common tech skills
    tech_skills = [
        'python', 'javascript', 'react', 'node.js', 'java', 'c++', 'c#', 'go', 'rust',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'postgresql', 'mysql', 'mongodb',
        'machine learning', 'ai', 'data science', 'sql', 'html', 'css', 'typescript',
        'swift', 'kotlin', 'android', 'ios', 'flutter', 'react native'
    ]
    
    for skill in tech_skills:
        if skill in content_lower:
            skills.append(skill.title())
    
    return skills

def _extract_requirements(content: str) -> List[str]:
    """Extract requirements from job content"""
    requirements = []
    content_lower = content.lower()
    
    # Common requirements
    if 'gpa' in content_lower:
        requirements.append('GPA 3.0+')
    if 'computer science' in content_lower:
        requirements.append('Computer Science or related field')
    if 'experience' in content_lower:
        requirements.append('Relevant experience required')
    if 'currently enrolled' in content_lower:
        requirements.append('Currently enrolled student')
    
    return requirements
