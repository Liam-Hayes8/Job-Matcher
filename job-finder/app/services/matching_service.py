import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from app.services.embedding_service import EmbeddingService
from app.core.config import settings

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.skill_keywords = self._load_skill_keywords()
        
    async def initialize(self):
        """Initialize the matching service"""
        await self.embedding_service.initialize()
        logger.info("Matching service initialized")
    
    def _load_skill_keywords(self) -> Dict[str, List[str]]:
        """Load skill keywords for different categories"""
        return {
            "programming_languages": [
                "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "php", "ruby",
                "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css", "bash", "powershell"
            ],
            "frameworks": [
                "react", "angular", "vue", "node.js", "express", "django", "flask", "spring", "laravel",
                "rails", "asp.net", "fastapi", "gin", "echo", "fiber", "actix", "rocket", "axum"
            ],
            "databases": [
                "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb",
                "firebase", "supabase", "cockroachdb", "timescaledb", "influxdb", "neo4j"
            ],
            "cloud_platforms": [
                "aws", "gcp", "azure", "digitalocean", "heroku", "vercel", "netlify", "cloudflare",
                "linode", "vultr", "scaleway", "ovh", "alibaba cloud"
            ],
            "devops_tools": [
                "docker", "kubernetes", "terraform", "ansible", "jenkins", "gitlab", "github actions",
                "circleci", "travis ci", "argo cd", "helm", "prometheus", "grafana", "elk stack"
            ],
            "ml_ai": [
                "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn",
                "jupyter", "hugging face", "openai", "vertex ai", "sagemaker", "mlflow", "kubeflow"
            ],
            "methodologies": [
                "agile", "scrum", "kanban", "lean", "devops", "ci/cd", "tdd", "bdd", "pair programming",
                "code review", "git flow", "trunk based development"
            ]
        }
    
    async def rank_jobs(
        self,
        resume_embedding: List[float],
        jobs: List[Dict[str, Any]],
        job_embeddings: List[List[float]],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Rank jobs by similarity to resume"""
        try:
            if not jobs or not job_embeddings:
                return []
            
            # Calculate similarity scores
            matches = []
            for i, job in enumerate(jobs):
                if i < len(job_embeddings):
                    similarity_score = self.embedding_service.calculate_similarity(
                        resume_embedding, job_embeddings[i]
                    )
                    
                    # Extract skills from job description
                    job_skills = self._extract_skills(job.get("description", ""))
                    
                    # Calculate skill match
                    resume_skills = self._extract_skills(job.get("resume_text", ""))
                    matching_skills = list(set(job_skills) & set(resume_skills))
                    
                    # Calculate experience match
                    experience_match = self._calculate_experience_match(
                        job.get("description", ""), job.get("resume_text", "")
                    )
                    
                    # Combined score (weighted average)
                    combined_score = (
                        similarity_score * 0.6 +
                        (len(matching_skills) / max(len(job_skills), 1)) * 0.3 +
                        experience_match * 0.1
                    )
                    
                    matches.append({
                        **job,
                        "match_score": combined_score,
                        "similarity_score": similarity_score,
                        "matching_skills": matching_skills,
                        "experience_match": experience_match,
                        "job_skills": job_skills
                    })
            
            # Filter by minimum threshold
            threshold = settings.min_similarity_threshold
            filtered_matches = [m for m in matches if m["match_score"] >= threshold]
            
            # Sort by combined score (descending)
            filtered_matches.sort(key=lambda x: x["match_score"], reverse=True)
            
            # Apply limit
            return filtered_matches[:limit]
            
        except Exception as e:
            logger.error(f"Error ranking jobs: {e}")
            return []
    
    async def rank_cached_jobs(
        self,
        resume_embedding: List[float],
        cached_jobs: List[Dict[str, Any]],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Rank cached jobs by similarity to resume"""
        try:
            if not cached_jobs:
                return []
            
            # Calculate similarity scores
            matches = []
            for job in cached_jobs:
                embedding = job.get("embedding")
                if not embedding:
                    continue
                
                similarity_score = self.embedding_service.calculate_similarity(
                    resume_embedding, embedding
                )
                
                # Extract skills
                job_skills = self._extract_skills(job.get("description", ""))
                resume_skills = self._extract_skills(job.get("resume_text", ""))
                matching_skills = list(set(job_skills) & set(resume_skills))
                
                # Calculate experience match
                experience_match = self._calculate_experience_match(
                    job.get("description", ""), job.get("resume_text", "")
                )
                
                # Combined score
                combined_score = (
                    similarity_score * 0.6 +
                    (len(matching_skills) / max(len(job_skills), 1)) * 0.3 +
                    experience_match * 0.1
                )
                
                matches.append({
                    **job,
                    "match_score": combined_score,
                    "similarity_score": similarity_score,
                    "matching_skills": matching_skills,
                    "experience_match": experience_match
                })
            
            # Filter and sort
            threshold = settings.min_similarity_threshold
            filtered_matches = [m for m in matches if m["match_score"] >= threshold]
            filtered_matches.sort(key=lambda x: x["match_score"], reverse=True)
            
            return filtered_matches[:limit]
            
        except Exception as e:
            logger.error(f"Error ranking cached jobs: {e}")
            return []
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        if not text:
            return []
        
        text_lower = text.lower()
        skills = []
        
        # Extract skills from all categories
        for category, keywords in self.skill_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    skills.append(keyword)
        
        # Extract additional skills using regex patterns
        # Programming languages
        lang_patterns = [
            r'\b(?:proficient in|experience with|skilled in)\s+([a-zA-Z+#]+)',
            r'\b([a-zA-Z+#]+)\s+(?:developer|programming|development)',
            r'\b(?:worked with|used)\s+([a-zA-Z+#]+)'
        ]
        
        for pattern in lang_patterns:
            matches = re.findall(pattern, text_lower)
            skills.extend(matches)
        
        # Remove duplicates and normalize
        skills = list(set([skill.lower().strip() for skill in skills if len(skill) > 1]))
        
        return skills
    
    def _calculate_experience_match(self, job_description: str, resume_text: str) -> float:
        """Calculate experience level match between job and resume"""
        try:
            # Extract experience indicators from job description
            job_experience_keywords = [
                "entry level", "junior", "mid level", "senior", "lead", "principal",
                "years of experience", "experience required", "minimum experience"
            ]
            
            job_desc_lower = job_description.lower()
            resume_lower = resume_text.lower()
            
            # Check for experience level in job description
            job_level = "entry"
            for keyword in job_experience_keywords:
                if keyword in job_desc_lower:
                    if "senior" in keyword or "lead" in keyword or "principal" in keyword:
                        job_level = "senior"
                    elif "mid" in keyword:
                        job_level = "mid"
                    elif "junior" in keyword or "entry" in keyword:
                        job_level = "entry"
                    break
            
            # Check for experience indicators in resume
            resume_experience_indicators = [
                "senior", "lead", "principal", "architect", "manager", "director",
                "years of experience", "experience", "worked", "developed", "managed"
            ]
            
            resume_level = "entry"
            experience_count = 0
            
            for indicator in resume_experience_indicators:
                if indicator in resume_lower:
                    experience_count += 1
                    if indicator in ["senior", "lead", "principal", "architect", "manager", "director"]:
                        resume_level = "senior"
                    elif experience_count > 3:
                        resume_level = "mid"
            
            # Calculate match score
            if job_level == resume_level:
                return 1.0
            elif (job_level == "senior" and resume_level == "mid") or (job_level == "mid" and resume_level == "senior"):
                return 0.7
            elif (job_level == "entry" and resume_level == "mid") or (job_level == "mid" and resume_level == "entry"):
                return 0.5
            else:
                return 0.3
                
        except Exception as e:
            logger.error(f"Error calculating experience match: {e}")
            return 0.5
    
    async def get_cached_job_count(self) -> int:
        """Get the number of cached jobs (placeholder)"""
        # This would typically query the database
        return 0
    
    async def get_last_refresh_time(self) -> Optional[datetime]:
        """Get the last cache refresh time (placeholder)"""
        # This would typically query the database
        return None
    
    def calculate_job_freshness_score(self, posted_at: datetime) -> float:
        """Calculate freshness score based on posting date"""
        try:
            now = datetime.utcnow()
            days_old = (now - posted_at).days
            
            if days_old <= 1:
                return 1.0
            elif days_old <= 3:
                return 0.9
            elif days_old <= 7:
                return 0.8
            elif days_old <= 14:
                return 0.6
            elif days_old <= 30:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Error calculating freshness score: {e}")
            return 0.5
    
    def enhance_job_matching(
        self,
        jobs: List[Dict[str, Any]],
        resume_text: str,
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhance job matching with additional preferences"""
        try:
            enhanced_jobs = []
            
            for job in jobs:
                score = job.get("match_score", 0)
                
                # Apply preference adjustments
                if preferences.get("remote_only") and not job.get("remote", False):
                    score *= 0.5
                
                if preferences.get("min_salary") and job.get("salary_min"):
                    if job["salary_min"] < preferences["min_salary"]:
                        score *= 0.7
                
                if preferences.get("max_salary") and job.get("salary_max"):
                    if job["salary_max"] > preferences["max_salary"]:
                        score *= 0.8
                
                if preferences.get("job_types") and job.get("job_type"):
                    if job["job_type"] not in preferences["job_types"]:
                        score *= 0.6
                
                # Apply freshness bonus
                freshness_score = self.calculate_job_freshness_score(job.get("posted_at", datetime.utcnow()))
                score *= (0.9 + freshness_score * 0.1)  # 10% weight for freshness
                
                enhanced_jobs.append({
                    **job,
                    "match_score": min(score, 1.0)  # Cap at 1.0
                })
            
            # Re-sort by enhanced score
            enhanced_jobs.sort(key=lambda x: x["match_score"], reverse=True)
            
            return enhanced_jobs
            
        except Exception as e:
            logger.error(f"Error enhancing job matching: {e}")
            return jobs
