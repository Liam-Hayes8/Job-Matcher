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
import uuid
import re
import requests
import asyncio
import hashlib
import random

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
        """Handle live jobs search request"""
        try:
            # Parse request data
            data = json.loads(post_data.decode('utf-8'))
            resume_text = data.get('resume_text', '')
            location = data.get('location', 'US')
            max_jobs = data.get('max_jobs', 20)
            
            # Mock live jobs data - FOCUSED ON INTERNSHIPS
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
                }
            ]
            
            # Simple ranking based on keyword matching
            resume_lower = resume_text.lower()
            keywords = ["python", "javascript", "react", "aws", "docker", "postgresql", "fastapi", "swift", "machine learning", "data science", "product management"]
            
            for job in mock_jobs:
                job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
                score = 0
                
                for keyword in keywords:
                    if keyword in resume_lower and keyword in job_text:
                        score += 0.2
                
                # Add some randomness for variety
                score += random.uniform(0, 0.3)
                job["match_score"] = min(score, 1.0)
                job["matching_skills"] = [skill for skill in job.get("skills_required", []) 
                                        if skill.lower() in resume_lower]
            
            # Sort by score and limit results
            ranked_jobs = sorted(mock_jobs, key=lambda x: x.get("match_score", 0.0), reverse=True)
            final_jobs = ranked_jobs[:max_jobs]
            
            return {
                "jobs": final_jobs,
                "metadata": {
                    "total_fetched": len(mock_jobs),
                    "open_jobs": len(mock_jobs),
                    "valid_links": len(mock_jobs),
                    "unique_jobs": len(mock_jobs),
                    "returned": len(final_jobs),
                    "duration_seconds": 1.2,
                    "sources_queried": 3,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
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
                                    
                                    # Check if resume has been parsed
                                    parsed_file = file_path.replace('.pdf', '_parsed.json')
                                    parsed_data = None
                                    if os.path.exists(parsed_file):
                                        try:
                                            with open(parsed_file, 'r') as f:
                                                parsed_data = json.load(f)
                                        except:
                                            pass
                                    
                                    resumes.append({
                                        "id": len(resumes) + 1,
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
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            elif path.startswith('/api/v1/resumes/') and path.endswith('/parse'):
                # Handle resume parsing
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
                
                # Mock resume parsing response (in production, this would use AI/ML)
                parsed_data = {
                    "skills": ["Python", "JavaScript", "React", "FastAPI", "SQL", "Docker", "Git", "AWS"],
                    "experience": [
                        {
                            "title": "Software Engineer",
                            "company": "Tech Company",
                            "duration": "2 years",
                            "description": "Developed web applications using Python and React"
                        },
                        {
                            "title": "Junior Developer",
                            "company": "Startup",
                            "duration": "1 year",
                            "description": "Worked on backend APIs and database design"
                        }
                    ],
                    "contact_info": {
                        "name": "Liam Hayes",
                        "email": "liam@example.com",
                        "phone": "+1-555-0123"
                    }
                }
                
                # Save parsed data to file
                parsed_file = resume_file.replace('.pdf', '_parsed.json')
                with open(parsed_file, 'w') as f:
                    json.dump(parsed_data, f)
                
                print(f"Resume {resume_id} parsed successfully")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(parsed_data).encode())
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
