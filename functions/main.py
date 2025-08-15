import json
import functions_framework
from google.cloud import storage
import tempfile
import os

@functions_framework.cloud_event
def parse_resume(cloud_event):
    """Cloud Function to parse resume PDF and extract text."""
    
    # Get the bucket and file information from the Cloud Event
    bucket_name = cloud_event.data["bucket"]
    file_name = cloud_event.data["name"]
    
    # Initialize Cloud Storage client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    # Download the file to a temporary location
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        blob.download_to_filename(temp_file.name)
        
        # For now, just return a simple response
        # In a real implementation, you would use a PDF parsing library
        result = {
            "filename": file_name,
            "status": "processed",
            "text": "Resume text would be extracted here",
            "skills": ["Python", "JavaScript", "React"],
            "experience": "5 years"
        }
    
    # Store the result back to Cloud Storage
    result_bucket = storage_client.bucket(f"{bucket_name}-results")
    result_blob = result_bucket.blob(f"{file_name}.json")
    result_blob.upload_from_string(json.dumps(result), content_type='application/json')
    
    return result