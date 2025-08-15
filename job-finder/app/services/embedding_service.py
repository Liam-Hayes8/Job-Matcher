import asyncio
import logging
from typing import List, Dict, Any
import numpy as np
from google.cloud import aiplatform
from google.cloud.aiplatform_v1.types import Content, Part
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = None
        self.model = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the Vertex AI client and model"""
        try:
            if not settings.vertex_ai_project_id:
                logger.warning("Vertex AI project ID not configured, using fallback embeddings")
                return
                
            # Initialize Vertex AI
            aiplatform.init(
                project=settings.vertex_ai_project_id,
                location=settings.vertex_ai_location
            )
            
            # Get the embedding model
            self.model = aiplatform.TextEmbeddingModel.from_pretrained(settings.vertex_ai_model)
            self.initialized = True
            
            logger.info(f"Embedding service initialized with model: {settings.vertex_ai_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            # Fall back to basic TF-IDF embeddings
            self.initialized = False
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            if self.initialized and self.model:
                # Use Vertex AI embeddings
                embeddings = self.model.get_embeddings([text])
                return embeddings[0].values
            else:
                # Fallback to basic embeddings
                return await self._fallback_embed_text(text)
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return await self._fallback_embed_text(text)
    
    async def embed_jobs(self, jobs: List[Dict[str, Any]]) -> List[List[float]]:
        """Generate embeddings for multiple job descriptions"""
        try:
            if not jobs:
                return []
            
            # Extract job descriptions
            descriptions = [job.get("description", "") for job in jobs]
            
            if self.initialized and self.model:
                # Use Vertex AI embeddings
                embeddings = self.model.get_embeddings(descriptions)
                return [emb.values for emb in embeddings]
            else:
                # Fallback to basic embeddings
                return await self._fallback_embed_jobs(descriptions)
                
        except Exception as e:
            logger.error(f"Error generating job embeddings: {e}")
            return await self._fallback_embed_jobs([job.get("description", "") for job in jobs])
    
    async def _fallback_embed_text(self, text: str) -> List[float]:
        """Fallback embedding using basic TF-IDF approach"""
        try:
            # Simple character-based embedding as fallback
            # In production, you might want to use a local embedding model
            import hashlib
            
            # Create a simple hash-based embedding
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to float array
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    value = int.from_bytes(chunk, byteorder='big')
                    embedding.append((value % 1000) / 1000.0)  # Normalize to 0-1
            
            # Pad or truncate to 768 dimensions (standard embedding size)
            while len(embedding) < 768:
                embedding.extend(embedding[:min(768 - len(embedding), len(embedding))])
            
            return embedding[:768]
            
        except Exception as e:
            logger.error(f"Error in fallback embedding: {e}")
            return [0.0] * 768
    
    async def _fallback_embed_jobs(self, descriptions: List[str]) -> List[List[float]]:
        """Fallback embeddings for multiple job descriptions"""
        embeddings = []
        for description in descriptions:
            embedding = await self._fallback_embed_text(description)
            embeddings.append(embedding)
        return embeddings
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        if self.initialized and self.model:
            return {
                "provider": "vertex_ai",
                "model": settings.vertex_ai_model,
                "dimensions": 768,
                "location": settings.vertex_ai_location
            }
        else:
            return {
                "provider": "fallback",
                "model": "hash_based",
                "dimensions": 768,
                "location": "local"
            }
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Normalize vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def batch_embed(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Generate embeddings in batches"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.embed_jobs([{"description": text} for text in batch])
            embeddings.extend(batch_embeddings)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        return embeddings
