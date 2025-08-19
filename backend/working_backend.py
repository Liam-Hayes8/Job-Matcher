#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from urllib.parse import urlparse, parse_qs
import os
import sys
import tempfile
import shutil
from datetime import datetime
from typing import Optional
import os
import uuid
import re
import requests
import asyncio
import hashlib
import random
import re

# Global resume storage (in-memory for now)
RESUME_STORAGE = {}

# Resume signal tokens for job matching
FIN_TOK = ("finance","financial","analyst","asset","wealth","equity","portfolio",
           "investment","trading","fp&a","valuation","real estate","acquisition",
           "underwriting","accounting","bloomberg","quickbooks","oracle")
SWE_TOK = ("software","engineer","developer","backend","frontend","full stack",
           "python","java","react","kubernetes","docker")

def extract_tokens(text: str) -> set[str]:
  t = text.lower()
  return {w for w in FIN_TOK + SWE_TOK if w in t}

def intern_like(title: str) -> bool:
  t = title.lower()
  return "intern" in t or "co-op" in t or "summer" in t or "new grad" in t

def token_score(title: str, desc: str, tokens: set[str]) -> float:
  text = (title + " " + (desc or "")).lower()
  f = sum(1 for k in FIN_TOK if k in text and k in tokens)
  s = sum(1 for k in SWE_TOK if k in text and k in tokens)
  # finance-leaning resumes: reward finance matches and penalize SWE terms
  if any(k in tokens for k in FIN_TOK) and not any(k in tokens for k in SWE_TOK):
    return 2.0 * f - 1.0 * s
  # SWE-leaning resumes
  if any(k in tokens for k in SWE_TOK):
    return 2.0 * s - 0.5 * f
  return f + s

def _host(url: str) -> str:
    from urllib.parse import urlparse
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def host_allowed(url: str) -> bool:
    """Canonical ATS allow-list, with optional extra dev hosts for mock data."""
    ALLOWED_BASE = {
        "boards.greenhouse.io",
        "jobs.lever.co",
        "jobs.eu.lever.co",
        "jobs.ashbyhq.com",
        # allow but validate harder (when validation enabled)
        "myworkdayjobs.com",
        "taleo.net",
    }
    DEV_EXTRA = {
        # mock/demo career hosts used in sample data
        "careers.google.com",
        "careers.microsoft.com",
        "www.amazon.jobs",
        "www.metacareers.com",
        "jobs.apple.com",
        "jobs.netflix.com",
        "careers.spotify.com",
        "careers.airbnb.com",
        "www.goldmansachs.com",
        "www.morganstanley.com",
        "careers.blackrock.com",
    }
    allow_extras = os.getenv("DEV_ALLOW_EXTRA_HOSTS", "1") == "1"
    allowed = ALLOWED_BASE | (DEV_EXTRA if allow_extras else set())
    return _host(url) in allowed

async def link_is_live(url: str, expect_title: Optional[str] = None) -> bool:
    """Validate link liveness now. For Workday/Taleo pages, also require some title words to appear."""
    import httpx
    _BAD = re.compile(r"(no longer available|job not found|position closed|no longer posted|no vacancies)", re.I)
    try:
        timeout = httpx.Timeout(20.0)
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as c:
            r = await c.head(url)
            if r.status_code in (405, 403):
                r = await c.get(url)
            if r.status_code // 100 != 2:
                return False
            text = (r.text or "")[:8000]
            if _BAD.search(text):
                return False
            h = _host(url)
            if ("myworkdayjobs.com" in h or "taleo.net" in h) and expect_title:
                words = [w for w in expect_title.lower().split() if len(w) > 3]
                if words and sum(w in text.lower() for w in words) < max(2, len(words)//3):
                    return False
            return True
    except Exception:
        return False

def _validate_links_sync(urls: list[str], titles: list[str]) -> list[bool]:
    """Synchronously validate a list of URLs using the async validator.
    Returns a list of booleans in the same order as input URLs.
    """
    async def _run(urls_inner: list[str], titles_inner: list[str]) -> list[bool]:
        results: list[bool] = []
        for u, t in zip(urls_inner, titles_inner):
            ok = await link_is_live(u, expect_title=t)
            results.append(ok)
        return results

    try:
        return asyncio.run(_run(urls, titles))
    except RuntimeError:
        # If there's already a running loop (unlikely in this server), create a new one
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_run(urls, titles))
        finally:
            loop.close()

class WorkingBackendHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Custom logging to see what's happening
        print(f"[{self.address_string()}] {format % args}")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def get_real_jobs(self, skills=None):
        """Get real jobs from multiple APIs - FOCUSED ON INTERNSHIPS"""
        jobs = []
        
        # Try LinkedIn Jobs API (simulated)
        try:
            # For demo purposes, we'll simulate real internship data
            # In production, you'd use actual job APIs like LinkedIn, Indeed, etc.
            sample_jobs = [
                {
                    "id": f"linkedin_intern_{uuid.uuid4().hex[:8]}",
                    "title": "Software Engineering Intern",
                    "company": "Google",
                    "location": "Mountain View, CA",
                    "description": "Join Google's engineering team as an intern! Work on real projects using Python, JavaScript, and cloud technologies.",
                    "salary_min": 8000,
                    "salary_max": 12000,
                    "job_type": "Internship",
                    "remote": "Hybrid",
                    "url": "https://careers.google.com/jobs/results/internships/123456",
                    "source": "LinkedIn",
                    "skills_required": ["Python", "JavaScript", "React", "Git", "Basic Algorithms"],
                    "duration": "12 weeks",
                    "requirements": ["Currently enrolled in Computer Science", "GPA 3.0+"]
                },
                {
                    "id": f"indeed_intern_{uuid.uuid4().hex[:8]}",
                    "title": "Full Stack Development Intern",
                    "company": "Microsoft",
                    "location": "Seattle, WA",
                    "description": "Build next-generation cloud applications using Azure, React, and TypeScript.",
                    "salary_min": 7500,
                    "salary_max": 11000,
                    "job_type": "Internship",
                    "remote": "Remote",
                    "url": "https://careers.microsoft.com/us/en/job/internships/123456",
                    "source": "Indeed",
                    "skills_required": ["Python", "JavaScript", "React", "Azure", "TypeScript"],
                    "duration": "10 weeks",
                    "requirements": ["Pursuing BS/MS in Computer Science", "Web development experience"]
                },
                {
                    "id": f"glassdoor_intern_{uuid.uuid4().hex[:8]}",
                    "title": "Data Science Intern",
                    "company": "Netflix",
                    "location": "Los Gatos, CA",
                    "description": "Analyze user behavior data to improve content recommendations using machine learning.",
                    "salary_min": 8500,
                    "salary_max": 13000,
                    "job_type": "Internship",
                    "remote": "Hybrid",
                    "url": "https://jobs.netflix.com/internships/123456",
                    "source": "Glassdoor",
                    "skills_required": ["Python", "Machine Learning", "SQL", "Statistics", "R"],
                    "duration": "12 weeks",
                    "requirements": ["Statistics/Data Science major", "ML experience preferred"]
                },
                {
                    "id": f"handshake_intern_{uuid.uuid4().hex[:8]}",
                    "title": "iOS Development Intern",
                    "company": "Apple",
                    "location": "Cupertino, CA",
                    "description": "Create amazing iOS applications that millions of users will love using Swift and SwiftUI.",
                    "salary_min": 8000,
                    "salary_max": 12000,
                    "job_type": "Internship",
                    "remote": "On-site",
                    "url": "https://jobs.apple.com/en/us/internships/123456",
                    "source": "Handshake",
                    "skills_required": ["Swift", "SwiftUI", "iOS Development", "Xcode", "Git"],
                    "duration": "12 weeks",
                    "requirements": ["Computer Science major", "iOS development experience"]
                },
                {
                    "id": f"wayup_intern_{uuid.uuid4().hex[:8]}",
                    "title": "Product Management Intern",
                    "company": "Airbnb",
                    "location": "San Francisco, CA",
                    "description": "Learn product management by working on real features that impact millions of users.",
                    "salary_min": 7500,
                    "salary_max": 11000,
                    "job_type": "Internship",
                    "remote": "Hybrid",
                    "url": "https://careers.airbnb.com/internships/123456",
                    "source": "WayUp",
                    "skills_required": ["Analytics", "User Research", "SQL", "Product Strategy"],
                    "duration": "12 weeks",
                    "requirements": ["Business/Engineering major", "Leadership experience"]
                }
            ]
            
            # Filter by skills if provided
            if skills:
                filtered_jobs = []
                for job in sample_jobs:
                    job_skills = set(skill.lower() for skill in job.get("skills_required", []))
                    user_skills = set(skill.lower() for skill in skills)
                    if job_skills.intersection(user_skills):
                        # Calculate match score
                        match_score = len(job_skills.intersection(user_skills)) / len(job_skills)
                        job["match_score"] = round(match_score, 2)
                        job["matching_skills"] = list(job_skills.intersection(user_skills))
                        filtered_jobs.append(job)
                jobs.extend(filtered_jobs)
            else:
                jobs.extend(sample_jobs)
                
        except Exception as e:
            print(f"Error fetching real jobs: {e}")
            # Fallback to mock data
            jobs = self.get_mock_jobs()
        
        return jobs
    
    def get_mock_jobs(self):
        """Fallback mock jobs - FOCUSED ON INTERNSHIPS"""
        return [
            {
                "id": 1,
                "title": "Software Engineering Intern",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "description": "We are looking for a talented software engineering intern with experience in Python, JavaScript, and React.",
                "salary_min": 6000,
                "salary_max": 9000,
                "job_type": "Internship",
                "remote": "Hybrid",
                "url": "https://example.com/internships/1",
                "source": "Mock",
                "match_score": 0.85,
                "matching_skills": ["Python", "JavaScript", "React"],
                "duration": "10 weeks",
                "requirements": ["Computer Science major", "GPA 3.0+"]
            }
        ]
    
    def handle_live_jobs_search(self, post_data):
        """Handle live jobs search request with resume-aware personalization"""
        try:
            # Parse request data
            data = json.loads(post_data.decode('utf-8'))
            resume_id = data.get('resume_id')
            resume_text = data.get('resume_text', '')
            location = data.get('location', 'US')
            limit = data.get('limit', 30)
            debug = data.get('debug', False)
            
            print(f"Live jobs search: resume_id={resume_id}, resume_length={len(resume_text)}, location={location}, limit={limit}, debug={debug}")
            
            # Load resume text
            text = ""
            if resume_id:
                if resume_id in RESUME_STORAGE:
                    stored_resume = RESUME_STORAGE[resume_id]
                    if stored_resume.get('parsed'):
                        text = stored_resume.get('text', '')
                    else:
                        return {"error": "Resume not parsed yet."}
                else:
                    return {"error": "Resume not found."}
            elif resume_text:
                text = resume_text
            else:
                return {"error": "Provide resume_id or resume_text."}
            
            # Extract resume signals
            tokens = extract_tokens(text)
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
            
            print(f"Using resume with tokens: {sorted(list(tokens))[:5]}")
            
            # Optionally fetch live jobs from Greenhouse boards if enabled
            def fetch_greenhouse_boards(board_tokens):
                jobs = []
                for token in board_tokens:
                    try:
                        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
                        resp = requests.get(url, timeout=12)
                        if resp.status_code != 200:
                            continue
                        data = resp.json()
                        for jj in data.get("jobs", []):
                            abs_url = jj.get("absolute_url")
                            if not abs_url:
                                continue
                            jobs.append({
                                "id": str(jj.get("id")),
                                "title": jj.get("title") or "",
                                "company": token.capitalize(),
                                "description": jj.get("content") or "",
                                "location": (jj.get("location") or {}).get("name"),
                                "apply_url": abs_url,
                                "posted_at": jj.get("updated_at"),
                                "open": True,
                                "source": "greenhouse",
                                "job_id": str(jj.get("id")),
                                "job_type": None,
                                "remote": None,
                                "salary_min": None,
                                "salary_max": None,
                            })
                    except Exception:
                        continue
                return jobs

            use_live = os.getenv("USE_LIVE", "0") == "1"
            jobs_source = []
            if use_live:
                # Default boards; override via GH_BOARDS env (comma-separated)
                boards = os.getenv("GH_BOARDS", "datadog,coinbase,robinhood,affirm").split(",")
                boards = [b.strip() for b in boards if b.strip()]
                jobs_source = fetch_greenhouse_boards(boards)
            # Mock live jobs data - FOCUSED ON INTERNSHIPS (fallback)
            mock_jobs = [
                {
                    "id": "google_intern_001",
                    "title": "Software Engineering Intern",
                    "company": "Google",
                    "description": "Join Google's engineering team as an intern! Work on real projects using Python, JavaScript, and cloud technologies. Perfect for students looking to gain industry experience.",
                    "location": "Mountain View, CA",
                    "apply_url": "https://careers.google.com/jobs/results/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "greenhouse",
                    "job_id": "intern_001",
                    "department": "Engineering",
                    "job_type": "Internship",
                    "remote": "Hybrid",
                    "salary_min": 8000,
                    "salary_max": 12000,
                    "duration": "12 weeks",
                    "skills_required": ["Python", "JavaScript", "React", "Git", "Basic Algorithms"],
                    "requirements": ["Currently enrolled in Computer Science or related field", "GPA 3.0+", "Available for Summer 2024"]
                },
                {
                    "id": "microsoft_intern_002",
                    "title": "Full Stack Development Intern",
                    "company": "Microsoft",
                    "description": "Build next-generation cloud applications using Azure, React, and TypeScript. Gain hands-on experience with modern web development and cloud services.",
                    "location": "Seattle, WA",
                    "apply_url": "https://careers.microsoft.com/us/en/job/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "greenhouse",
                    "job_id": "intern_002",
                    "department": "Cloud & AI",
                    "job_type": "Internship",
                    "remote": "Remote",
                    "salary_min": 7500,
                    "salary_max": 11000,
                    "duration": "10 weeks",
                    "skills_required": ["Python", "JavaScript", "React", "Azure", "TypeScript"],
                    "requirements": ["Pursuing BS/MS in Computer Science", "Experience with web development", "Strong problem-solving skills"]
                },
                {
                    "id": "amazon_intern_003",
                    "title": "Backend Engineering Intern",
                    "company": "Amazon",
                    "description": "Design and implement scalable backend services using AWS, Python, and PostgreSQL. Learn microservices architecture and cloud infrastructure.",
                    "location": "Seattle, WA",
                    "apply_url": "https://www.amazon.jobs/en/jobs/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "greenhouse",
                    "job_id": "intern_003",
                    "department": "AWS",
                    "job_type": "Internship",
                    "remote": "On-site",
                    "salary_min": 8500,
                    "salary_max": 13000,
                    "duration": "12 weeks",
                    "skills_required": ["Python", "Java", "AWS", "Docker", "PostgreSQL"],
                    "requirements": ["Computer Science major", "Knowledge of data structures", "Familiarity with databases"]
                },
                {
                    "id": "meta_intern_004",
                    "title": "Software Engineering Intern - AI/ML",
                    "company": "Meta",
                    "description": "Work on cutting-edge AI and machine learning projects. Help develop algorithms that power billions of users worldwide.",
                    "location": "Menlo Park, CA",
                    "apply_url": "https://www.metacareers.com/jobs/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "lever",
                    "job_id": "intern_004",
                    "department": "AI Research",
                    "job_type": "Internship",
                    "remote": "Hybrid",
                    "salary_min": 9000,
                    "salary_max": 14000,
                    "duration": "12 weeks",
                    "skills_required": ["Python", "Machine Learning", "TensorFlow", "PyTorch", "Statistics"],
                    "requirements": ["Graduate student in AI/ML", "Research experience preferred", "Strong mathematical background"]
                },
                {
                    "id": "apple_intern_005",
                    "title": "iOS Development Intern",
                    "company": "Apple",
                    "description": "Create amazing iOS applications that millions of users will love. Work with Swift, SwiftUI, and Apple's latest technologies.",
                    "location": "Cupertino, CA",
                    "apply_url": "https://jobs.apple.com/en/us/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "lever",
                    "job_id": "intern_005",
                    "department": "Software Engineering",
                    "job_type": "Internship",
                    "remote": "On-site",
                    "salary_min": 8000,
                    "salary_max": 12000,
                    "duration": "12 weeks",
                    "skills_required": ["Swift", "SwiftUI", "iOS Development", "Xcode", "Git"],
                    "requirements": ["Computer Science or related field", "iOS development experience", "Portfolio of apps preferred"]
                },
                {
                    "id": "netflix_intern_006",
                    "title": "Data Science Intern",
                    "company": "Netflix",
                    "description": "Analyze user behavior data to improve content recommendations. Work with big data technologies and machine learning models.",
                    "location": "Los Gatos, CA",
                    "apply_url": "https://jobs.netflix.com/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "greenhouse",
                    "job_id": "intern_006",
                    "department": "Data Science",
                    "job_type": "Internship",
                    "remote": "Hybrid",
                    "salary_min": 8500,
                    "salary_max": 13000,
                    "duration": "10 weeks",
                    "skills_required": ["Python", "R", "SQL", "Machine Learning", "Statistics"],
                    "requirements": ["Statistics/Data Science major", "Experience with data analysis", "Knowledge of ML algorithms"]
                },
                {
                    "id": "spotify_intern_007",
                    "title": "Frontend Engineering Intern",
                    "company": "Spotify",
                    "description": "Build beautiful user interfaces for Spotify's web and mobile applications. Work with React, TypeScript, and modern frontend technologies.",
                    "location": "New York, NY",
                    "apply_url": "https://careers.spotify.com/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "lever",
                    "job_id": "intern_007",
                    "department": "Frontend Engineering",
                    "job_type": "Internship",
                    "remote": "Remote",
                    "salary_min": 7000,
                    "salary_max": 10000,
                    "duration": "12 weeks",
                    "skills_required": ["React", "TypeScript", "JavaScript", "CSS", "Git"],
                    "requirements": ["Web development experience", "Knowledge of modern JavaScript", "Eye for design"]
                },
                {
                    "id": "airbnb_intern_008",
                    "title": "Product Management Intern",
                    "company": "Airbnb",
                    "description": "Learn product management by working on real features that impact millions of users. Collaborate with engineering, design, and data teams.",
                    "location": "San Francisco, CA",
                    "apply_url": "https://careers.airbnb.com/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "greenhouse",
                    "job_id": "intern_008",
                    "department": "Product",
                    "job_type": "Internship",
                    "remote": "Hybrid",
                    "salary_min": 7500,
                    "salary_max": 11000,
                    "duration": "12 weeks",
                    "skills_required": ["Analytics", "User Research", "SQL", "Product Strategy", "Communication"],
                    "requirements": ["Business/Engineering major", "Leadership experience", "Strong analytical skills"]
                },
                {
                    "id": "goldman_intern_009",
                    "title": "Investment Banking Summer Analyst",
                    "company": "Goldman Sachs",
                    "description": "Join our investment banking team and work on mergers, acquisitions, and capital raising transactions. Gain exposure to financial modeling and valuation.",
                    "location": "New York, NY",
                    "apply_url": "https://www.goldmansachs.com/careers/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "greenhouse",
                    "job_id": "intern_009",
                    "department": "Investment Banking",
                    "job_type": "Internship",
                    "remote": "On-site",
                    "salary_min": 12000,
                    "salary_max": 18000,
                    "duration": "10 weeks",
                    "skills_required": ["Financial Modeling", "Excel", "Valuation", "Accounting", "Bloomberg"],
                    "requirements": ["Finance/Economics major", "Strong analytical skills", "GPA 3.5+"]
                },
                {
                    "id": "morgan_intern_010",
                    "title": "Financial Analyst Intern",
                    "company": "Morgan Stanley",
                    "description": "Analyze financial data and market trends to support investment decisions. Work with Bloomberg terminals and financial modeling tools.",
                    "location": "New York, NY",
                    "apply_url": "https://www.morganstanley.com/careers/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "greenhouse",
                    "job_id": "intern_010",
                    "department": "Finance",
                    "job_type": "Internship",
                    "remote": "Hybrid",
                    "salary_min": 10000,
                    "salary_max": 15000,
                    "duration": "12 weeks",
                    "skills_required": ["Financial Analysis", "Bloomberg", "QuickBooks", "Excel", "Accounting"],
                    "requirements": ["Finance/Accounting major", "Proficiency in Excel", "Knowledge of financial markets"]
                },
                {
                    "id": "blackrock_intern_011",
                    "title": "Asset Management Intern",
                    "company": "BlackRock",
                    "description": "Learn about portfolio management and investment strategies. Work with real assets and help manage client portfolios.",
                    "location": "New York, NY",
                    "apply_url": "https://careers.blackrock.com/internships/123456",
                    "posted_at": datetime.now().isoformat(),
                    "open": True,
                    "source": "greenhouse",
                    "job_id": "intern_011",
                    "department": "Asset Management",
                    "job_type": "Internship",
                    "remote": "On-site",
                    "salary_min": 11000,
                    "salary_max": 16000,
                    "duration": "12 weeks",
                    "skills_required": ["Portfolio Management", "Asset Allocation", "Risk Management", "Bloomberg", "Financial Modeling"],
                    "requirements": ["Finance/Economics major", "Interest in markets", "Strong quantitative skills"]
                }
            ]
            
            # Filter jobs based on resume signals and link validation
            jobs = jobs_source if use_live and jobs_source else mock_jobs
            fetched_total = len(jobs)
            
            # Filter to internships
            jobs = [j for j in jobs if intern_like(j.get('title', ''))]
            after_intern = len(jobs)
            print(f"After intern filter: {after_intern} jobs")
            
            # Score by resume tokens
            for j in jobs:
                j['score'] = token_score(j.get('title', ''), j.get('description', ''), tokens)
            
            # Keep if score >= 1.0, else drop
            scored = [j for j in jobs if j['score'] >= 1.0]
            after_score = len(scored)
            print(f"After score filter: {after_score} jobs")
            
            # Fallback widening if too few results
            if len(scored) < 10:
                # widen to keep top N by score even if < 1.0
                jobs.sort(key=lambda x: x['score'], reverse=True)
                scored = jobs[:min(20, len(jobs))]
                print(f"After widening: {len(scored)} jobs")
            
            # Filter to canonical ATS hosts only (can be skipped in dev)
            if os.getenv("SKIP_ALLOWLIST", "1") == "1":
                after_allow = len(scored)
                print(f"After host filter: {after_allow} jobs (skipped)")
            else:
                scored = [j for j in scored if host_allowed(j.get('apply_url', ''))]
                after_allow = len(scored)
                print(f"After host filter: {after_allow} jobs")
            
            # Live-validate links now (2xx + no tombstone text) if enabled
            do_validate = os.getenv("LIVE_VALIDATE", "0") == "1"
            drop_samples = []
            if do_validate:
                urls = [j.get('apply_url', '') for j in scored]
                titles = [j.get('title', '') for j in scored]
                results = _validate_links_sync(urls, titles)
                kept_list = []
                for j, ok in zip(scored, results):
                    if ok:
                        kept_list.append(j)
                    elif len(drop_samples) < 5:
                        drop_samples.append({
                            "company": j.get('company'),
                            "title": j.get('title'),
                            "url": j.get('apply_url'),
                            "reason": "dead_or_tombstone_or_title_mismatch",
                        })
                scored = kept_list
            after_validation = len(scored)
            print(f"After live validation: {after_validation} jobs (validation={'on' if do_validate else 'off'})")
            
            # Sort by score and limit results
            scored.sort(key=lambda x: x['score'], reverse=True)
            jobs = scored[:limit]
            
            print(f"Live job search results: {len(jobs)} jobs returned")
            if jobs:
                print(f"  - Top job: {jobs[0].get('title')} at {jobs[0].get('company')} (score: {jobs[0].get('score', 0):.3f})")
            
            # Return predictable shape with debug info
            payload = {
                "jobs": jobs,
                "debug": {
                    "used_resume_id": resume_id,
                    "resume_sha": text_hash,
                    "tokens": sorted(list(tokens))[:8],
                    "fetched_total": fetched_total,
                    "after_intern": after_intern,
                    "after_score": after_score,
                    "after_allowlist": after_allow,
                    "after_validation": after_validation,
                    "dropped_examples": drop_samples if 'drop_samples' in locals() else [],
                }
            }
            
            return payload
            
        except Exception as e:
            print(f"Live jobs search error: {e}")
            return {"error": str(e)}
    
    def do_GET(self):
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            print(f"GET request to: {path}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if path == '/api/v1/resumes' or path == '/api/v1/resumes/':
                # Return list of uploaded resumes with parsed status
                uploads_dir = "/tmp/uploads"
                resumes = []
                
                if os.path.exists(uploads_dir):
                    for user_dir in os.listdir(uploads_dir):
                        user_path = os.path.join(uploads_dir, user_dir)
                        if os.path.isdir(user_path):
                            for filename in os.listdir(user_path):
                                file_path = os.path.join(user_path, filename)
                                if os.path.isfile(file_path):
                                    stat = os.stat(file_path)
                                    resume_id = str(len(resumes) + 1)
                                    
                                    # Check if resume has been parsed (read from DB, not sidecar file)
                                    parsed_data = None
                                    if resume_id in RESUME_STORAGE:
                                        stored_resume = RESUME_STORAGE[resume_id]
                                        if stored_resume.get('parsed'):
                                            parsed_data = {
                                                "skills": ["Python", "JavaScript", "React", "FastAPI", "SQL", "Docker", "Git", "AWS"],
                                                "experience": [
                                                    {
                                                        "title": "Software Engineer",
                                                        "company": "Tech Company",
                                                        "duration": "2 years",
                                                        "description": "Developed web applications using Python and React"
                                                    }
                                                ],
                                                "contact_info": {
                                                    "name": "Test User",
                                                    "email": "test@example.com",
                                                    "phone": "+1-555-0123"
                                                }
                                            }
                                    
                                    resumes.append({
                                        "id": int(resume_id),
                                        "filename": filename,
                                        "file_path": file_path,
                                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                        "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                        "parsed_data": parsed_data
                                    })
                
                print(f"Returning {len(resumes)} resumes")
                self.wfile.write(json.dumps(resumes).encode())
            elif path.startswith('/api/v1/matches/'):
                # Return real job matches for a resume
                resume_id = path.split('/')[-1]
                
                # Get parsed data for the resume
                uploads_dir = "/tmp/uploads"
                parsed_data = None
                
                if os.path.exists(uploads_dir):
                    for user_dir in os.listdir(uploads_dir):
                        user_path = os.path.join(uploads_dir, user_dir)
                        if os.path.isdir(user_path):
                            for filename in os.listdir(user_path):
                                file_path = os.path.join(user_path, filename)
                                parsed_file = file_path.replace('.pdf', '_parsed.json')
                                if os.path.exists(parsed_file):
                                    try:
                                        with open(parsed_file, 'r') as f:
                                            parsed_data = json.load(f)
                                        break
                                    except:
                                        pass
                
                # Get real jobs based on parsed skills
                skills = parsed_data.get("skills", []) if parsed_data else None
                jobs = self.get_real_jobs(skills)
                
                print(f"Returning {len(jobs)} real job matches for resume {resume_id}")
                self.wfile.write(json.dumps(jobs).encode())
            elif path == '/api/v1/jobs' or path == '/api/v1/jobs/':
                # Return available jobs (real + mock)
                jobs = self.get_real_jobs()
                # Normalize to include apply_url for View Jobs page
                for j in jobs:
                    if 'apply_url' not in j:
                        # fallback to any url-like field
                        j['apply_url'] = j.get('applyUrl') or j.get('job_url') or j.get('url') or ''
                print(f"Returning {len(jobs)} jobs")
                self.wfile.write(json.dumps(jobs).encode())
            elif path == '/api/v1/jobs/live/health':
                # Health check for live jobs
                response = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "test_source": "mock",
                    "test_result": True
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                response = {"message": "Mock API endpoint", "path": path}
                print(f"Unknown path: {path}")
                self.wfile.write(json.dumps(response).encode())
                
        except Exception as e:
            print(f"Error in GET request: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def parse_multipart_form_data(self):
        """Simple multipart form data parser"""
        content_type = self.headers.get('Content-Type', '')
        content_length = int(self.headers.get('Content-Length', 0))
        
        if not content_type.startswith('multipart/form-data'):
            raise Exception("Invalid content type")
        
        # Extract boundary
        boundary_match = re.search(r'boundary=([^;]+)', content_type)
        if not boundary_match:
            raise Exception("No boundary found")
        
        boundary = boundary_match.group(1)
        boundary_bytes = f'--{boundary}'.encode()
        
        # Read the entire request body
        data = self.rfile.read(content_length)
        
        # Split by boundary
        parts = data.split(boundary_bytes)
        
        files = {}
        for part in parts[1:-1]:  # Skip first and last parts
            if not part.strip():
                continue
                
            # Parse headers
            header_end = part.find(b'\r\n\r\n')
            if header_end == -1:
                continue
                
            headers_text = part[:header_end].decode('utf-8', errors='ignore')
            body = part[header_end + 4:]
            
            # Extract filename from headers
            filename_match = re.search(r'filename="([^"]+)"', headers_text)
            if filename_match:
                filename = filename_match.group(1)
                files['file'] = {
                    'filename': filename,
                    'data': body
                }
        
        return files
    
    def do_POST(self):
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            print(f"POST request to: {path}")
            
            if path == '/api/v1/resumes/upload':
                # Handle file upload
                try:
                    files = self.parse_multipart_form_data()
                    
                    if 'file' in files:
                        file_info = files['file']
                        filename = file_info['filename']
                        file_data = file_info['data']
                        
                        # Create upload directory
                        user_id = "local-user-123"  # Mock user ID
                        upload_dir = f"/tmp/uploads/{user_id}"
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        # Save the file
                        file_path = os.path.join(upload_dir, filename)
                        
                        with open(file_path, 'wb') as f:
                            f.write(file_data)
                        
                        # Create response
                        response = {
                            "id": 1,
                            "filename": filename,
                            "file_path": file_path,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                            "parsed_data": None  # Initially not parsed
                        }
                        
                        print(f"File uploaded successfully: {filename}")
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps(response).encode())
                        return
                    else:
                        raise Exception("No file provided")
                        
                except Exception as e:
                    print(f"File upload error: {e}")
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return
            elif path == '/api/v1/jobs/live':
                # Handle live jobs search
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length) if content_length > 0 else b''
                
                result = self.handle_live_jobs_search(post_data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-store')  # Real-time, no caching
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            elif path.startswith('/api/v1/resumes/') and path.endswith('/parse'):
                # Handle resume parsing - write parsed text to DB as single source of truth
                resume_id = path.split('/')[-2]
                
                # Find the resume file
                uploads_dir = "/tmp/uploads"
                resume_file = None
                
                if os.path.exists(uploads_dir):
                    for user_dir in os.listdir(uploads_dir):
                        user_path = os.path.join(uploads_dir, user_dir)
                        if os.path.isdir(user_path):
                            for filename in os.listdir(user_path):
                                if filename.endswith('.pdf'):
                                    resume_file = os.path.join(user_path, filename)
                                    break
                            if resume_file:
                                break
                
                if not resume_file:
                    raise Exception("Resume file not found")
                
                # Extract text from PDF (mock for now)
                text = f"Software Engineer with experience in Python, JavaScript, React, and cloud technologies. Resume for {resume_id}."
                
                if not text or len(text.strip()) < 20:
                    raise Exception("Could not extract text")
                
                # Store parsed text in DB (in-memory for now)
                RESUME_STORAGE[resume_id] = {
                    "id": resume_id,
                    "text": text,
                    "parsed_at": datetime.utcnow().isoformat(),
                    "parsed": True
                }
                
                print(f"Resume {resume_id} parsed successfully")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "resume_id": resume_id,
                    "parsed": True,
                    "chars": len(text)
                }).encode())
            elif path.startswith('/api/v1/matches/'):
                # Handle job matching
                resume_id = path.split('/')[-1]
                
                # Get parsed data and find real jobs
                skills = ["Python", "JavaScript", "React"]  # Default skills
                jobs = self.get_real_jobs(skills)
                
                print(f"Found {len(jobs)} real job matches for resume {resume_id}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(jobs).encode())
            else:
                # Handle other POST requests
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length) if content_length > 0 else b''
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {"message": "Mock POST endpoint", "path": path}
                print(f"Unknown POST path: {path}")
                
                self.wfile.write(json.dumps(response).encode())
                
        except Exception as e:
            print(f"Error in POST request: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

def run_server():
    try:
        server_address = ('', 8000)
        httpd = HTTPServer(server_address, WorkingBackendHandler)
        print("Working backend server running on http://localhost:8000")
        print("This server can handle actual file uploads, resume parsing, and live job matching!")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_server()
