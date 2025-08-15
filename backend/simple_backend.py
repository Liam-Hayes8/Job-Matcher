from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from urllib.parse import urlparse, parse_qs
import os
import sys

class MockBackendHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Custom logging to see what's happening
        print(f"[{self.address_string()}] {format % args}")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
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
                # Mock resumes data
                response = [
                    {
                        "id": 1,
                        "filename": "sample_resume.pdf",
                        "upload_date": "2024-01-15T10:30:00Z",
                        "status": "processed",
                        "parsed_data": True
                    }
                ]
                print(f"Returning resumes: {response}")
            elif path.startswith('/api/v1/matches/'):
                # Mock job matches data
                response = [
                    {
                        "id": 1,
                        "job_listing": {
                            "title": "Software Engineer",
                            "company": "Tech Corp",
                            "location": "San Francisco, CA",
                            "description": "We are looking for a talented software engineer...",
                            "salary_min": 80000,
                            "salary_max": 120000,
                            "job_type": "Full-time",
                            "remote": "Hybrid"
                        },
                        "match_score": 0.85,
                        "matching_skills": ["Python", "JavaScript", "React", "FastAPI"]
                    },
                    {
                        "id": 2,
                        "job_listing": {
                            "title": "Full Stack Developer",
                            "company": "Startup Inc",
                            "location": "Remote",
                            "description": "Join our growing team as a full stack developer...",
                            "salary_min": 70000,
                            "salary_max": 100000,
                            "job_type": "Full-time",
                            "remote": "Remote"
                        },
                        "match_score": 0.78,
                        "matching_skills": ["Python", "JavaScript", "SQL", "Docker"]
                    }
                ]
                print(f"Returning matches: {len(response)} matches")
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
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            print(f"POST request to: {path}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if path == '/api/v1/resumes/upload':
                # Mock file upload response
                response = {
                    "message": "Resume uploaded successfully",
                    "resume_id": 1,
                    "filename": "uploaded_resume.pdf"
                }
                print(f"File upload response: {response}")
            elif path.startswith('/api/v1/matches/find/'):
                # Mock job matching response
                response = {
                    "message": "Job matches found successfully",
                    "matches_count": 5,
                    "resume_id": 1
                }
                print(f"Job matching response: {response}")
            else:
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
        httpd = HTTPServer(server_address, MockBackendHandler)
        print("Mock backend server running on http://localhost:8000")
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
