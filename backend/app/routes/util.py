import httpx
import logging
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
import numpy as np
from google.cloud import aiplatform
import os

logger = logging.getLogger(__name__)

# Initialize Vertex AI
try:
    aiplatform.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
except Exception as e:
    logger.warning(f"Vertex AI initialization failed: {e}")

async def head_ok(client: httpx.AsyncClient, url: str) -> bool:
    """
    Validate that a job application URL is accessible.
    HEAD request with fallback to GET, follows redirects.
    """
    if not url:
        return False
    
    try:
        # Try HEAD first
        response = await client.head(url, timeout=5)
        if response.status_code in [200, 201, 202]:
            return True
        
        # Fallback to GET if HEAD not supported
        response = await client.get(url, timeout=5)
        if response.status_code in [200, 201, 202]:
            return True
            
        return False
        
    except httpx.TimeoutException:
        logger.debug(f"Timeout validating URL: {url}")
        return False
    except httpx.HTTPStatusError as e:
        logger.debug(f"HTTP error validating URL {url}: {e.response.status_code}")
        return False
    except Exception as e:
        logger.debug(f"Error validating URL {url}: {e}")
        return False

def dedupe_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Remove duplicate jobs based on title, company, and location.
    """
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        # Create a unique key for each job
        key = hashlib.md5(
            f"{job.get('title', '')}{job.get('company', '')}{job.get('location', '')}".encode()
        ).hexdigest()
        
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    return unique_jobs

def embed_resume(resume_text: str) -> Optional[List[float]]:
    """
    Generate embeddings for resume text using Vertex AI.
    """
    try:
        if not resume_text:
            return None
            
        # Use Vertex AI Text Embeddings API
        model = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
        embeddings = model.get_embeddings([resume_text])
        
        if embeddings and len(embeddings) > 0:
            return embeddings[0].values
        return None
        
    except Exception as e:
        logger.warning(f"Failed to embed resume: {e}")
        return None

def embed_jobs(jobs: List[Dict], cache: bool = False) -> List[Dict]:
    """
    Generate embeddings for job descriptions and add to job objects.
    Optionally cache vectors in database.
    """
    try:
        model = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
        
        # Prepare texts for embedding
        texts = []
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')}"
            texts.append(text)
        
        # Get embeddings in batch
        embeddings = model.get_embeddings(texts)
        
        # Add embeddings to jobs
        for i, job in enumerate(jobs):
            if i < len(embeddings):
                job["embedding"] = embeddings[i].values
                
                # Cache in database if requested
                if cache:
                    _cache_job_vector(job)
        
        return jobs
        
    except Exception as e:
        logger.warning(f"Failed to embed jobs: {e}")
        return jobs

def rank(resume_vector: List[float], jobs: List[Dict]) -> List[Dict]:
    """
    Rank jobs by cosine similarity to resume vector.
    """
    if not resume_vector or not jobs:
        return jobs
    
    try:
        # Calculate cosine similarities
        for job in jobs:
            if "embedding" in job and job["embedding"]:
                similarity = cosine_similarity(resume_vector, job["embedding"])
                job["similarity_score"] = similarity
            else:
                job["similarity_score"] = 0.0
        
        # Sort by similarity score (descending)
        ranked_jobs = sorted(jobs, key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        
        return ranked_jobs
        
    except Exception as e:
        logger.warning(f"Failed to rank jobs: {e}")
        return jobs

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    """
    try:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    except Exception as e:
        logger.warning(f"Failed to calculate cosine similarity: {e}")
        return 0.0

def _cache_job_vector(job: Dict):
    """
    Cache job vector in database for reuse.
    This would integrate with your database schema.
    """
    try:
        # This is a placeholder - implement based on your database setup
        # Example with SQLAlchemy:
        # job_vector = JobVector(
        #     job_id=job.get("job_id"),
        #     company=job.get("company"),
        #     title=job.get("title"),
        #     embedding=job.get("embedding"),
        #     created_at=datetime.now()
        # )
        # db.add(job_vector)
        # db.commit()
        pass
        
    except Exception as e:
        logger.warning(f"Failed to cache job vector: {e}")

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skills from text using simple keyword matching.
    In production, use NLP libraries or AI services.
    """
    # Common tech skills
    skills = [
        "python", "javascript", "java", "c++", "c#", "go", "rust", "php", "ruby", "swift",
        "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "git", "jenkins", "github", "gitlab", "bitbucket",
        "html", "css", "sass", "less", "typescript", "webpack", "babel",
        "machine learning", "ai", "tensorflow", "pytorch", "scikit-learn",
        "data science", "pandas", "numpy", "matplotlib", "seaborn"
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return list(set(found_skills))  # Remove duplicates
