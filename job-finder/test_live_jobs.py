#!/usr/bin/env python3
"""
Test script for the live jobs endpoint
"""
import asyncio
import httpx
import json
from datetime import datetime

async def test_live_jobs():
    """Test the live jobs endpoint"""
    
    # Test data
    test_request = {
        "resume_text": "Computer Science student with Python, JavaScript, and React experience. Looking for internship opportunities.",
        "location": "US",
        "max_jobs": 5,
        "timeout": 12
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test health check
            print("Testing health check...")
            health_response = await client.get("http://localhost:8080/api/v1/jobs/live/health")
            print(f"Health check status: {health_response.status_code}")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"Health data: {json.dumps(health_data, indent=2)}")
            
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
    asyncio.run(test_live_jobs())
