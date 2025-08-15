#!/usr/bin/env python3
"""
Simple test script for job-finder service
"""
import asyncio
import httpx
import json
from datetime import datetime

async def test_simple():
    """Test basic functionality"""
    
    # Test data
    test_request = {
        "resume_text": "Computer Science student with Python, JavaScript, and React experience. Looking for internship opportunities.",
        "location": "US",
        "max_jobs": 3,
        "timeout": 12
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test basic health
            print("Testing basic health...")
            health_response = await client.get("http://localhost:8080/health")
            print(f"Basic health status: {health_response.status_code}")
            if health_response.status_code == 200:
                print(f"Basic health: {health_response.json()}")
            
            # Test live jobs health
            print("\nTesting live jobs health...")
            live_health_response = await client.get("http://localhost:8080/api/v1/jobs/live/health")
            print(f"Live jobs health status: {live_health_response.status_code}")
            if live_health_response.status_code == 200:
                print(f"Live jobs health: {live_health_response.json()}")
            else:
                print(f"Live jobs health error: {live_health_response.text}")
            
            # Test live jobs search
            print("\nTesting live jobs search...")
            start_time = datetime.now()
            
            response = await client.post(
                "http://localhost:8080/api/v1/jobs/live",
                json=test_request,
                timeout=30
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            print(f"Request completed in {duration:.2f} seconds")
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Jobs returned: {len(data.get('jobs', []))}")
                print(f"Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")
                
                # Show first job details
                if data.get('jobs'):
                    first_job = data['jobs'][0]
                    print(f"\nFirst job:")
                    print(f"  Title: {first_job.get('title')}")
                    print(f"  Company: {first_job.get('company')}")
                    print(f"  Apply URL: {first_job.get('apply_url')}")
                    print(f"  Match Score: {first_job.get('match_score', 0)}")
                    print(f"  Source: {first_job.get('source')}")
            else:
                print(f"Error response: {response.text}")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple())
