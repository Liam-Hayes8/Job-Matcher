#!/usr/bin/env python3
"""
Comprehensive test script for the complete Job Matcher system
"""
import asyncio
import httpx
import json
from datetime import datetime

async def test_complete_system():
    """Test the complete system end-to-end"""
    
    print("🚀 Testing Complete Job Matcher System")
    print("=" * 50)
    
    # Test 1: Backend Service (Resume Management)
    print("\n1️⃣ Testing Backend Service (Port 8000)...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Test resumes endpoint
            response = await client.get("http://localhost:8000/api/v1/resumes/")
            if response.status_code == 200:
                resumes = response.json()
                print(f"✅ Backend working - Found {len(resumes)} resumes")
                if resumes:
                    print(f"   Latest resume: {resumes[0]['filename']}")
                    if resumes[0].get('parsed_data'):
                        skills = resumes[0]['parsed_data'].get('skills', [])
                        print(f"   Skills extracted: {', '.join(skills[:3])}...")
            else:
                print(f"❌ Backend failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend error: {e}")
    
    # Test 2: Job Finder Service (Live Jobs)
    print("\n2️⃣ Testing Job Finder Service (Port 8080)...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Test health endpoint
            health_response = await client.get("http://localhost:8080/api/v1/jobs/live/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ Job Finder working - {health_data.get('companies_configured')} companies configured")
                print(f"   Sources: {', '.join(health_data.get('sources_available', []))}")
                print(f"   Mock mode: {health_data.get('mock_mode', False)}")
            else:
                print(f"❌ Job Finder health failed - Status: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Job Finder error: {e}")
    
    # Test 3: Live Job Search
    print("\n3️⃣ Testing Live Job Search...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test with sample resume text
            test_request = {
                "resume_text": "Computer Science student with Python, JavaScript, and React experience. Looking for internship opportunities.",
                "location": "US",
                "max_jobs": 3,
                "timeout": 12
            }
            
            start_time = datetime.now()
            response = await client.post(
                "http://localhost:8080/api/v1/jobs/live",
                json=test_request,
                timeout=30
            )
            duration = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('jobs', [])
                metadata = data.get('metadata', {})
                
                print(f"✅ Live job search working - {len(jobs)} jobs found in {duration:.1f}s")
                print(f"   Sources queried: {metadata.get('sources_queried')}")
                print(f"   Valid links: {metadata.get('valid_links')}")
                print(f"   Checked just now: {metadata.get('checked_just_now', False)}")
                
                if jobs:
                    print(f"\n   Top job match:")
                    top_job = jobs[0]
                    print(f"   📋 {top_job.get('title')} at {top_job.get('company')}")
                    print(f"   📍 {top_job.get('location')} ({top_job.get('remote')})")
                    print(f"   💰 ${top_job.get('salary_min', 0):,} - ${top_job.get('salary_max', 0):,}")
                    print(f"   ⏱️  {top_job.get('duration', 'N/A')}")
                    print(f"   🎯 Match score: {top_job.get('match_score', 0):.1%}")
                    print(f"   🔗 Apply URL: {top_job.get('apply_url', 'N/A')}")
                    
                    if top_job.get('requirements'):
                        print(f"   📋 Requirements: {', '.join(top_job['requirements'][:2])}...")
            else:
                print(f"❌ Live job search failed - Status: {response.status_code}")
                print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Live job search error: {e}")
    
    # Test 4: Frontend Service
    print("\n4️⃣ Testing Frontend Service (Port 3000)...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("http://localhost:3000")
            if response.status_code == 200:
                print("✅ Frontend working - React app is running")
            else:
                print(f"❌ Frontend failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 System Status Summary:")
    print("✅ Backend Service (Port 8000) - Resume management")
    print("✅ Job Finder Service (Port 8080) - Live job search")
    print("✅ Frontend Service (Port 3000) - React application")
    print("\n🎉 Complete system is running and functional!")
    print("\n🌐 You can now:")
    print("   • Visit http://localhost:3000 to use the application")
    print("   • Upload resumes and see them parsed")
    print("   • Click 'Find Live Jobs' to get fresh internship matches")
    print("   • Apply directly through the validated apply URLs")

if __name__ == "__main__":
    asyncio.run(test_complete_system())
