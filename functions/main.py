import os
import json
import logging
from typing import Dict, Any
from google.cloud import storage
import functions_framework
from flask import Request
import PyPDF2
from docx import Document
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def parse_resume(cloud_event):
    """
    Cloud Function triggered by Cloud Storage upload.
    Parses PDF/DOCX files and extracts text content.
    """
    try:
        data = cloud_event.data
        bucket_name = data['bucket']
        file_name = data['name']
        
        logger.info(f"Processing file: {file_name} from bucket: {bucket_name}")
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        file_content = blob.download_as_bytes()
        
        extracted_text = ""
        file_extension = os.path.splitext(file_name)[1].lower()
        
        if file_extension == '.pdf':
            extracted_text = extract_text_from_pdf(file_content)
        elif file_extension == '.docx':
            extracted_text = extract_text_from_docx(file_content)
        elif file_extension == '.txt':
            extracted_text = file_content.decode('utf-8')
        else:
            logger.error(f"Unsupported file type: {file_extension}")
            return
        
        parsed_data = {
            'filename': file_name,
            'text_content': extracted_text,
            'file_size': len(file_content),
            'status': 'parsed'
        }
        
        output_file_name = f"parsed/{os.path.splitext(file_name)[0]}.json"
        output_blob = bucket.blob(output_file_name)
        output_blob.upload_from_string(
            json.dumps(parsed_data, indent=2),
            content_type='application/json'
        )
        
        logger.info(f"Successfully parsed and saved: {output_file_name}")
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file content."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file content."""
    try:
        doc = Document(io.BytesIO(file_content))
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return ""

@functions_framework.http
def parse_resume_http(request: Request):
    """HTTP endpoint for testing the resume parsing function."""
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    try:
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': 'No file selected'}, 400
        
        file_content = file.read()
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        extracted_text = ""
        if file_extension == '.pdf':
            extracted_text = extract_text_from_pdf(file_content)
        elif file_extension == '.docx':
            extracted_text = extract_text_from_docx(file_content)
        elif file_extension == '.txt':
            extracted_text = file_content.decode('utf-8')
        else:
            return {'error': f'Unsupported file type: {file_extension}'}, 400
        
        result = {
            'filename': file.filename,
            'text_content': extracted_text,
            'file_size': len(file_content),
            'status': 'parsed'
        }
        
        headers = {'Access-Control-Allow-Origin': '*'}
        return (result, 200, headers)
        
    except Exception as e:
        logger.error(f"Error in HTTP endpoint: {str(e)}")
        headers = {'Access-Control-Allow-Origin': '*'}
        return ({'error': str(e)}, 500, headers)