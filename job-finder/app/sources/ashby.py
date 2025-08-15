import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def fetch(client: httpx.AsyncClient, companies: List[Dict]) -> List[Dict]:
    """
    Fetch jobs from Ashby API for specified companies.
    Returns jobs with canonical apply URLs.
    """
    jobs = []
    
    for company in companies:
        if company.get('ats') != 'ashby':
            continue
            
        board_name = company.get('slug')
        if not board_name:
            logger.warning(f"No board name for company {company.get('name')}")
            continue
            
        try:
            # Ashby Job Postings API (GraphQL)
            url = "https://jobs.ashbyhq.com/api/non-user-graphql"
            
            query = """
            query JobBoardQuery($organizationHostedJobsPageName: String!, $organizationHostedJobsPageId: String!) {
                organizationHostedJobsPage(
                    organizationHostedJobsPageName: $organizationHostedJobsPageName
                    organizationHostedJobsPageId: $organizationHostedJobsPageId
                ) {
                    jobPostings {
                        id
                        title
                        descriptionHtml
                        locationName
                        applyUrl
                        updatedAt
                        isActive
                        departmentName
                        employmentType
                        compensationTierSummary
                    }
                }
            }
            """
            
            variables = {
                "organizationHostedJobsPageName": board_name,
                "organizationHostedJobsPageId": board_name
            }
            
            response = await client.post(
                url, 
                json={"query": query, "variables": variables},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            job_postings = data.get('data', {}).get('organizationHostedJobsPage', {}).get('jobPostings', [])
            
            for job in job_postings:
                # Only include jobs that are currently active
                if not job.get('isActive', False):
                    continue
                    
                # Get the canonical apply URL
                apply_url = job.get('applyUrl')
                if not apply_url:
                    continue
                
                # Parse location
                location = job.get('locationName', 'Remote')
                
                # Parse job type and remote status
                job_type = _extract_job_type(job)
                remote_status = _extract_remote_status(job)
                
                # Parse salary if available
                salary_min, salary_max = _extract_salary(job)
                
                # Extract skills from job description
                skills_required = _extract_skills(job.get('descriptionHtml', ''))
                
                jobs.append({
                    'id': f"ashby_{job['id']}",
                    'title': job.get('title', ''),
                    'company': company.get('name', ''),
                    'description': job.get('descriptionHtml', ''),
                    'location': location,
                    'apply_url': apply_url,
                    'posted_at': job.get('updatedAt', datetime.now().isoformat()),
                    'open': True,
                    'source': 'ashby',
                    'job_id': job['id'],
                    'department': job.get('departmentName', ''),
                    'job_type': job_type,
                    'remote': remote_status,
                    'salary_min': salary_min,
                    'salary_max': salary_max,
                    'skills_required': skills_required,
                    'requirements': _extract_requirements(job.get('descriptionHtml', ''))
                })
                
        except Exception as e:
            logger.error(f"Error fetching from Ashby for {company.get('name')}: {e}")
            continue
    
    return jobs

def _extract_job_type(job: Dict) -> str:
    """Extract job type from Ashby job data"""
    # Check for internship indicators
    title = job.get('title', '').lower()
    description = job.get('descriptionHtml', '').lower()
    employment_type = job.get('employmentType', '').lower()
    
    if any(word in title for word in ['intern', 'internship', 'co-op']):
        return 'Internship'
    elif any(word in description for word in ['intern', 'internship', 'co-op']):
        return 'Internship'
    elif 'intern' in employment_type:
        return 'Internship'
    else:
        return 'Full-time'

def _extract_remote_status(job: Dict) -> str:
    """Extract remote status from Ashby job data"""
    location = job.get('locationName', '').lower()
    description = job.get('descriptionHtml', '').lower()
    
    if 'remote' in location or 'remote' in description:
        return 'Remote'
    elif 'hybrid' in description:
        return 'Hybrid'
    else:
        return 'On-site'

def _extract_salary(job: Dict) -> tuple[Optional[int], Optional[int]]:
    """Extract salary range from Ashby job data"""
    compensation = job.get('compensationTierSummary', '')
    if not compensation:
        return None, None
    
    # Parse compensation string (e.g., "$80,000 - $120,000")
    import re
    salary_match = re.search(r'\$([0-9,]+)\s*-\s*\$([0-9,]+)', compensation)
    if salary_match:
        min_salary = int(salary_match.group(1).replace(',', ''))
        max_salary = int(salary_match.group(2).replace(',', ''))
        return min_salary, max_salary
    
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
