from typing import List, Dict, Any
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class ResumeService:
    def __init__(self):
        try:
            self.nlp = spacy.load(settings.SPACY_MODEL)
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            logger.info("Resume service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize resume service: {e}")
            raise

    def extract_skills(self, text: str) -> List[str]:
        doc = self.nlp(text)
        
        skills = []
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "LANGUAGE"]:
                skills.append(ent.text.lower())
        
        skill_keywords = [
            "python", "javascript", "java", "react", "nodejs", "sql", "docker",
            "kubernetes", "aws", "gcp", "azure", "tensorflow", "pytorch",
            "machine learning", "data science", "api", "rest", "graphql",
            "git", "agile", "scrum", "ci/cd", "devops"
        ]
        
        text_lower = text.lower()
        for keyword in skill_keywords:
            if keyword in text_lower:
                skills.append(keyword)
        
        return list(set(skills))

    def extract_experience(self, text: str) -> List[Dict[str, Any]]:
        doc = self.nlp(text)
        
        experiences = []
        
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(keyword in sent_text for keyword in ["worked", "experience", "developed", "managed", "led"]):
                for ent in sent.ents:
                    if ent.label_ == "ORG":
                        experiences.append({
                            "company": ent.text,
                            "description": sent.text.strip()
                        })
        
        return experiences

    def parse_resume_content(self, content: str) -> Dict[str, Any]:
        try:
            skills = self.extract_skills(content)
            experience = self.extract_experience(content)
            
            doc = self.nlp(content)
            
            contact_info = {}
            for ent in doc.ents:
                if ent.label_ == "PERSON" and not contact_info.get("name"):
                    contact_info["name"] = ent.text
                elif "@" in ent.text and not contact_info.get("email"):
                    contact_info["email"] = ent.text
            
            return {
                "skills": skills,
                "experience": experience,
                "contact_info": contact_info,
                "raw_text": content
            }
        except Exception as e:
            logger.error(f"Failed to parse resume content: {e}")
            raise

    def calculate_job_match_score(self, resume_data: Dict[str, Any], job_description: str) -> float:
        try:
            resume_text = " ".join([
                " ".join(resume_data.get("skills", [])),
                " ".join([exp.get("description", "") for exp in resume_data.get("experience", [])]),
                resume_data.get("raw_text", "")
            ])
            
            documents = [resume_text, job_description]
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            
            similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            score = float(similarity_matrix[0][0])
            
            return min(max(score, 0.0), 1.0)
        except Exception as e:
            logger.error(f"Failed to calculate job match score: {e}")
            return 0.0

    def get_matching_jobs(self, resume_data: Dict[str, Any], job_listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            matches = []
            
            for job in job_listings:
                score = self.calculate_job_match_score(resume_data, job.get("description", ""))
                
                matches.append({
                    **job,
                    "match_score": score,
                    "matching_skills": list(set(resume_data.get("skills", [])) & 
                                          set(self.extract_skills(job.get("description", ""))))
                })
            
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            return matches
        except Exception as e:
            logger.error(f"Failed to get matching jobs: {e}")
            return []

resume_service = ResumeService()